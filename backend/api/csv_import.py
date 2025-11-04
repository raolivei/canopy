from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List, Optional
import uuid
import time
from datetime import datetime
from backend.models.csv_import import (
    CSVImportConfig, CSVImportPreview, CSVImportRequest, 
    ImportResult, ImportHistory, ImportHistoryList,
    BankFormat, FieldMapping, ImportStatus
)
from backend.models.transaction import Transaction, TransactionCreate
from backend.services.csv_parser import CSVParserService
from backend.api.transactions import transactions_db, next_id

router = APIRouter(prefix="/v1/csv-import", tags=["csv-import"])

# Service instance
csv_service = CSVParserService()

# Storage for import previews and history
import_previews: dict[str, CSVImportPreview] = {}
import_history: List[ImportHistory] = []

@router.get("/formats", response_model=List[dict])
async def get_supported_formats():
    """Get list of supported bank formats"""
    formats = []
    for bank_format in BankFormat:
        format_info = {
            "id": bank_format.value,
            "name": bank_format.value.replace("_", " ").title(),
            "has_preset": bank_format in csv_service.BANK_FORMATS
        }
        formats.append(format_info)
    return formats

@router.get("/format/{bank_format}", response_model=dict)
async def get_format_config(bank_format: BankFormat):
    """Get field mapping configuration for a specific bank format"""
    if bank_format in csv_service.BANK_FORMATS:
        mapping = csv_service.BANK_FORMATS[bank_format]
        return {
            "bank_format": bank_format.value,
            "field_mapping": mapping.model_dump()
        }
    raise HTTPException(status_code=404, detail=f"No preset configuration for {bank_format.value}")

@router.post("/preview", response_model=dict)
async def preview_csv_import(
    file: UploadFile = File(...),
    bank_format: str = Form(BankFormat.GENERIC.value),
    default_currency: str = Form("USD"),
    default_account: Optional[str] = Form(None),
    skip_rows: int = Form(0),
    skip_duplicates: bool = Form(True)
):
    """
    Upload and preview a CSV file before importing.
    Returns a preview of transactions that will be imported.
    """
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Read file content
    try:
        content = await file.read()
        file_content = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Try to detect headers and format
    lines = file_content.strip().split('\n')
    if not lines:
        raise HTTPException(status_code=400, detail="File is empty")
    
    headers = lines[skip_rows].split(',')
    detected_format = csv_service.detect_bank_format(headers)
    
    # Get field mapping
    try:
        bank_format_enum = BankFormat(bank_format)
    except ValueError:
        bank_format_enum = BankFormat.GENERIC
    
    # Use preset mapping if available, otherwise require custom mapping
    if bank_format_enum in csv_service.BANK_FORMATS:
        field_mapping = csv_service.BANK_FORMATS[bank_format_enum]
    elif detected_format and detected_format in csv_service.BANK_FORMATS:
        field_mapping = csv_service.BANK_FORMATS[detected_format]
        bank_format_enum = detected_format
    else:
        # For generic format, try to infer from common column names
        field_mapping = _infer_field_mapping(headers)
    
    # Create import config
    config = CSVImportConfig(
        bank_format=bank_format_enum,
        field_mapping=field_mapping,
        default_currency=default_currency,
        default_account=default_account,
        skip_rows=skip_rows,
        skip_duplicates=skip_duplicates
    )
    
    # Parse and preview
    try:
        preview = csv_service.parse_csv_file(
            file_content=file_content,
            config=config,
            existing_transactions=transactions_db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    # Generate unique import ID
    import_id = str(uuid.uuid4())
    
    # Store preview for later import
    import_previews[import_id] = preview
    
    return {
        "import_id": import_id,
        "filename": file.filename,
        "detected_format": detected_format.value if detected_format else None,
        "used_format": bank_format_enum.value,
        "headers": headers,
        "preview": preview.model_dump(),
        "config": config.model_dump()
    }

@router.post("/import", response_model=ImportResult)
async def import_transactions(request: CSVImportRequest):
    """
    Import transactions from a previously previewed CSV file.
    """
    
    # Get preview
    preview = import_previews.get(request.import_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Import preview not found. Please upload and preview the file first.")
    
    start_time = time.time()
    
    # Convert preview to transactions
    transactions_to_create = csv_service.create_transactions_from_preview(
        preview=preview,
        skip_duplicates=request.skip_duplicates,
        skip_errors=request.skip_errors,
        selected_rows=request.selected_rows
    )
    
    # Import transactions
    imported_ids = []
    errors = []
    
    global next_id
    for tx_create in transactions_to_create:
        try:
            new_transaction = Transaction(
                id=next_id,
                description=tx_create.description,
                amount=tx_create.amount,
                currency=tx_create.currency,
                type=tx_create.type,
                category=tx_create.category,
                date=tx_create.date or datetime.now(),
                account=tx_create.account,
                merchant=tx_create.merchant,
                original_statement=tx_create.original_statement,
                notes=tx_create.notes,
                tags=tx_create.tags,
                ticker=tx_create.ticker,
            )
            next_id += 1
            transactions_db.append(new_transaction)
            imported_ids.append(new_transaction.id)
        except Exception as e:
            errors.append({
                "description": tx_create.description,
                "error": str(e)
            })
    
    duration = time.time() - start_time
    
    # Determine status
    status = ImportStatus.COMPLETED
    if errors:
        status = ImportStatus.PARTIALLY_COMPLETED if imported_ids else ImportStatus.FAILED
    
    # Create result
    result = ImportResult(
        import_id=request.import_id,
        status=status,
        total_rows=len(transactions_to_create) + len(errors),
        imported_count=len(imported_ids),
        skipped_count=preview.duplicate_rows if request.skip_duplicates else 0,
        error_count=len(errors),
        errors=errors,
        imported_transaction_ids=imported_ids,
        duration_seconds=duration
    )
    
    # Add to history
    # Note: We don't have filename here, would need to pass it in request or store in preview
    history_entry = ImportHistory(
        import_id=request.import_id,
        filename="imported_file.csv",  # TODO: Store filename in preview
        bank_format=BankFormat.GENERIC,  # TODO: Store format in preview
        status=status,
        total_rows=result.total_rows,
        imported_count=result.imported_count,
        skipped_count=result.skipped_count,
        error_count=result.error_count,
        created_at=result.created_at,
        completed_at=datetime.now()
    )
    import_history.append(history_entry)
    
    # Clean up preview after import
    if request.import_id in import_previews:
        del import_previews[request.import_id]
    
    return result

@router.get("/history", response_model=ImportHistoryList)
async def get_import_history(limit: int = 50, offset: int = 0):
    """Get import history"""
    
    # Sort by created_at descending
    sorted_history = sorted(
        import_history, 
        key=lambda x: x.created_at, 
        reverse=True
    )
    
    paginated = sorted_history[offset:offset + limit]
    
    return ImportHistoryList(
        imports=paginated,
        total=len(import_history)
    )

@router.get("/history/{import_id}", response_model=ImportHistory)
async def get_import_details(import_id: str):
    """Get details of a specific import"""
    
    for entry in import_history:
        if entry.import_id == import_id:
            return entry
    
    raise HTTPException(status_code=404, detail="Import not found")

@router.delete("/preview/{import_id}")
async def delete_preview(import_id: str):
    """Delete a preview that hasn't been imported yet"""
    
    if import_id in import_previews:
        del import_previews[import_id]
        return {"message": "Preview deleted"}
    
    raise HTTPException(status_code=404, detail="Preview not found")

@router.post("/custom-mapping", response_model=dict)
async def create_custom_mapping(
    file: UploadFile = File(...),
    date_column: str = Form(...),
    description_column: str = Form(...),
    amount_column: Optional[str] = Form(None),
    debit_column: Optional[str] = Form(None),
    credit_column: Optional[str] = Form(None),
    type_column: Optional[str] = Form(None),
    category_column: Optional[str] = Form(None),
    account_column: Optional[str] = Form(None),
    currency_column: Optional[str] = Form(None),
    date_format: str = Form("%Y-%m-%d"),
    default_currency: str = Form("USD"),
    default_account: Optional[str] = Form(None),
    skip_rows: int = Form(0)
):
    """
    Upload CSV with custom field mapping.
    Must specify either amount_column OR both debit_column and credit_column.
    """
    
    # Validate that we have amount info
    if not amount_column and not (debit_column and credit_column):
        raise HTTPException(
            status_code=400, 
            detail="Must provide either 'amount_column' or both 'debit_column' and 'credit_column'"
        )
    
    # Read file
    try:
        content = await file.read()
        file_content = content.decode('utf-8')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
    
    # Create custom field mapping
    field_mapping = FieldMapping(
        date_column=date_column,
        description_column=description_column,
        amount_column=amount_column or "",
        type_column=type_column,
        category_column=category_column,
        account_column=account_column,
        currency_column=currency_column,
        debit_column=debit_column,
        credit_column=credit_column,
        date_format=date_format
    )
    
    # Create config
    config = CSVImportConfig(
        bank_format=BankFormat.CUSTOM,
        field_mapping=field_mapping,
        default_currency=default_currency,
        default_account=default_account,
        skip_rows=skip_rows,
        skip_duplicates=True
    )
    
    # Parse and preview
    try:
        preview = csv_service.parse_csv_file(
            file_content=file_content,
            config=config,
            existing_transactions=transactions_db
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    # Generate import ID
    import_id = str(uuid.uuid4())
    import_previews[import_id] = preview
    
    return {
        "import_id": import_id,
        "filename": file.filename,
        "preview": preview.model_dump(),
        "config": config.model_dump()
    }

def _infer_field_mapping(headers: List[str]) -> FieldMapping:
    """Infer field mapping from headers for generic format"""
    headers_lower = [h.lower().strip() for h in headers]
    
    # Try to find date column
    date_column = None
    for h in headers:
        if any(word in h.lower() for word in ['date', 'posted', 'transaction date']):
            date_column = h
            break
    
    # Try to find description column
    description_column = None
    for h in headers:
        if any(word in h.lower() for word in ['description', 'memo', 'details', 'payee', 'merchant']):
            description_column = h
            break
    
    # Try to find amount column
    amount_column = None
    debit_column = None
    credit_column = None
    
    for h in headers:
        h_lower = h.lower()
        if 'debit' in h_lower:
            debit_column = h
        elif 'credit' in h_lower:
            credit_column = h
        elif any(word in h_lower for word in ['amount', 'value', 'total']):
            amount_column = h
    
    # If we have both debit and credit, prefer those
    if debit_column and credit_column:
        amount_column = ""  # Use debit/credit instead
    
    # Set defaults if not found
    date_column = date_column or headers[0]
    description_column = description_column or headers[1] if len(headers) > 1 else headers[0]
    
    if not amount_column and not (debit_column and credit_column):
        # Try to find any numeric-looking column
        amount_column = headers[-1] if headers else "Amount"
    
    return FieldMapping(
        date_column=date_column,
        description_column=description_column,
        amount_column=amount_column or "",
        debit_column=debit_column,
        credit_column=credit_column,
        date_format="%Y-%m-%d"  # Default
    )

