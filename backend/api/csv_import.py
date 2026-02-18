"""CSV Import API endpoints for importing transactions from bank exports."""

import uuid
import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from sqlalchemy import select, func

from backend.db.session import get_db_session
from backend.db.models.transaction import Transaction as TransactionModel
from backend.models.csv_import import (
    CSVImportConfig, CSVImportPreview, CSVImportRequest, 
    ImportResult, ImportHistory, ImportHistoryList,
    BankFormat, FieldMapping, ImportStatus
)
from backend.services.csv_parser import CSVParserService

router = APIRouter(prefix="/v1/csv-import", tags=["csv-import"])

# Service instance
csv_service = CSVParserService()

# Storage for import previews (temporary, cleared after import)
import_previews: dict[str, dict] = {}


@router.get("/formats", response_model=list[dict])
async def get_supported_formats():
    """Get list of supported bank formats."""
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
    """Get field mapping configuration for a specific bank format."""
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
    default_currency: str = Form("CAD"),
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
    
    # Parse and preview (no existing transactions to check against initially)
    try:
        preview = csv_service.parse_csv_file(
            file_content=file_content,
            config=config,
            existing_transactions=[]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    # Generate unique import ID
    import_id = str(uuid.uuid4())
    
    # Store preview for later import
    import_previews[import_id] = {
        "preview": preview,
        "config": config,
        "filename": file.filename,
        "bank_format": bank_format_enum,
    }
    
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
    Persists transactions to the database.
    """
    
    # Get preview
    preview_data = import_previews.get(request.import_id)
    if not preview_data:
        raise HTTPException(
            status_code=404, 
            detail="Import preview not found. Please upload and preview the file first."
        )
    
    preview = preview_data["preview"]
    filename = preview_data["filename"]
    bank_format = preview_data["bank_format"]
    
    start_time = time.time()
    
    # Convert preview to transaction create objects
    transactions_to_create = csv_service.create_transactions_from_preview(
        preview=preview,
        skip_duplicates=request.skip_duplicates,
        skip_errors=request.skip_errors,
        selected_rows=request.selected_rows
    )
    
    # Import transactions to database
    imported_ids = []
    errors = []
    
    with get_db_session() as db:
        for tx_create in transactions_to_create:
            try:
                new_tx = TransactionModel(
                    description=tx_create.description,
                    amount=Decimal(str(tx_create.amount)),
                    currency=tx_create.currency,
                    type=tx_create.type.value,
                    date=tx_create.date or datetime.now(),
                    category=tx_create.category,
                    account=tx_create.account,
                    merchant=tx_create.merchant,
                    original_statement=tx_create.original_statement,
                    notes=tx_create.notes,
                    tags=tx_create.tags,
                    ticker=tx_create.ticker,
                    shares=Decimal(str(tx_create.shares)) if tx_create.shares else None,
                    price_per_share=Decimal(str(tx_create.price_per_share)) if tx_create.price_per_share else None,
                    import_id=request.import_id,
                    import_source=bank_format.value,
                )
                db.add(new_tx)
                db.flush()  # Get the ID
                imported_ids.append(new_tx.id)
            except Exception as e:
                errors.append({
                    "description": tx_create.description,
                    "error": str(e)
                })
        
        db.commit()
    
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
    
    # Clean up preview after import
    if request.import_id in import_previews:
        del import_previews[request.import_id]
    
    return result


@router.get("/history", response_model=dict)
async def get_import_history(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get import history based on transactions with import_id."""
    with get_db_session() as db:
        # Get unique import_ids with counts
        query = (
            select(
                TransactionModel.import_id,
                TransactionModel.import_source,
                func.count(TransactionModel.id).label('count'),
                func.min(TransactionModel.date).label('earliest_date'),
                func.max(TransactionModel.date).label('latest_date'),
                func.min(TransactionModel.created_at).label('imported_at'),
            )
            .where(TransactionModel.import_id.isnot(None))
            .group_by(TransactionModel.import_id, TransactionModel.import_source)
            .order_by(func.min(TransactionModel.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
        
        results = db.execute(query).all()
        
        imports = [
            {
                "import_id": r.import_id,
                "source": r.import_source,
                "transaction_count": r.count,
                "date_range": {
                    "start": r.earliest_date.isoformat() if r.earliest_date else None,
                    "end": r.latest_date.isoformat() if r.latest_date else None,
                },
                "imported_at": r.imported_at.isoformat() if r.imported_at else None,
            }
            for r in results
        ]
        
        # Get total count
        total_query = (
            select(func.count(func.distinct(TransactionModel.import_id)))
            .where(TransactionModel.import_id.isnot(None))
        )
        total = db.execute(total_query).scalar() or 0
        
        return {
            "imports": imports,
            "total": total,
        }


@router.delete("/preview/{import_id}")
async def delete_preview(import_id: str):
    """Delete a preview that hasn't been imported yet."""
    
    if import_id in import_previews:
        del import_previews[import_id]
        return {"message": "Preview deleted"}
    
    raise HTTPException(status_code=404, detail="Preview not found")


@router.delete("/import/{import_id}")
async def delete_import(import_id: str):
    """Delete all transactions from a specific import."""
    with get_db_session() as db:
        # Count transactions to delete
        count_query = (
            select(func.count(TransactionModel.id))
            .where(TransactionModel.import_id == import_id)
        )
        count = db.execute(count_query).scalar() or 0
        
        if count == 0:
            raise HTTPException(status_code=404, detail="No transactions found for this import")
        
        # Delete transactions
        delete_query = (
            select(TransactionModel)
            .where(TransactionModel.import_id == import_id)
        )
        transactions = db.execute(delete_query).scalars().all()
        for tx in transactions:
            db.delete(tx)
        
        db.commit()
        
        return {"message": f"Deleted {count} transactions from import {import_id}"}


def _infer_field_mapping(headers: list[str]) -> FieldMapping:
    """Infer field mapping from headers for generic format."""
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
