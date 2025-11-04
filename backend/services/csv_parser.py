import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from backend.models.csv_import import (
    CSVImportConfig, TransactionPreview, CSVImportPreview, 
    FieldMapping, BankFormat, ImportResult, ImportStatus
)
from backend.models.transaction import Transaction, TransactionCreate, TransactionType

class CSVParserService:
    """Service for parsing CSV files and converting to transactions"""
    
    # Predefined bank formats with common field mappings
    BANK_FORMATS = {
        BankFormat.MONARCH: FieldMapping(
            date_column="Date",
            merchant_column="Merchant",
            description_column="Merchant",  # Use merchant as description too
            original_statement_column="Original Statement",
            notes_column="Notes",
            tags_column="Tags",
            amount_column="Amount",
            category_column="Category",
            account_column="Account",
            date_format="%Y-%m-%d",
            negative_means_expense=True
        ),
        BankFormat.CHASE: FieldMapping(
            date_column="Posting Date",
            description_column="Description",
            amount_column="Amount",
            type_column="Type",
            category_column="Category",
            balance_column="Balance",
            date_format="%m/%d/%Y"
        ),
        BankFormat.BANK_OF_AMERICA: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            balance_column="Running Bal.",
            date_format="%m/%d/%Y",
            negative_means_expense=True
        ),
        BankFormat.WELLS_FARGO: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            date_format="%m/%d/%Y",
            negative_means_expense=True
        ),
        BankFormat.AMEX: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            date_format="%m/%d/%Y",
            amount_is_absolute=True
        ),
        BankFormat.CAPITAL_ONE: FieldMapping(
            date_column="Transaction Date",
            description_column="Description",
            debit_column="Debit",
            credit_column="Credit",
            category_column="Category",
            date_format="%Y-%m-%d"
        ),
        BankFormat.TD_BANK: FieldMapping(
            date_column="Date",
            description_column="Description",
            debit_column="Debit",
            credit_column="Credit",
            date_format="%m/%d/%Y"
        ),
        BankFormat.RBC: FieldMapping(
            date_column="Transaction Date",
            description_column="Description",
            debit_column="Debit",
            credit_column="Credit",
            account_column="Account Number",
            date_format="%m/%d/%Y"
        ),
        BankFormat.NUBANK: FieldMapping(
            date_column="date",
            description_column="title",
            amount_column="amount",
            category_column="category",
            date_format="%Y-%m-%d",
            negative_means_expense=False
        ),
    }
    
    def __init__(self):
        self.import_cache: Dict[str, CSVImportPreview] = {}
        
    def detect_bank_format(self, headers: List[str]) -> Optional[BankFormat]:
        """Attempt to detect bank format from CSV headers"""
        headers_lower = [h.lower().strip() for h in headers]
        
        # Monarch Money detection (very specific pattern)
        if ("date" in headers_lower and "merchant" in headers_lower and 
            "category" in headers_lower and "account" in headers_lower and
            "original statement" in headers_lower):
            return BankFormat.MONARCH
        
        # Chase detection
        if "posting date" in headers_lower and "type" in headers_lower:
            return BankFormat.CHASE
            
        # Capital One detection
        if "transaction date" in headers_lower and "debit" in headers_lower:
            return BankFormat.CAPITAL_ONE
            
        # Nubank detection
        if "date" in headers_lower and "title" in headers_lower and "category" in headers_lower:
            return BankFormat.NUBANK
            
        # RBC detection
        if "account number" in headers_lower and "transaction date" in headers_lower:
            return BankFormat.RBC
            
        return None
        
    def parse_csv_file(
        self, 
        file_content: str, 
        config: CSVImportConfig,
        existing_transactions: List[Transaction] = None
    ) -> CSVImportPreview:
        """Parse CSV file and return preview of transactions"""
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(file_content))
        rows = list(csv_reader)
        
        if not rows:
            return CSVImportPreview(
                total_rows=0,
                valid_rows=0,
                duplicate_rows=0,
                error_rows=0,
                transactions=[]
            )
        
        # Skip specified rows
        if config.skip_rows > 0:
            rows = rows[config.skip_rows:]
        
        transactions: List[TransactionPreview] = []
        duplicate_count = 0
        error_count = 0
        
        existing_transactions = existing_transactions or []
        
        for idx, row in enumerate(rows):
            try:
                transaction = self._parse_row(
                    row, 
                    idx, 
                    config,
                    existing_transactions
                )
                transactions.append(transaction)
                
                if transaction.is_duplicate:
                    duplicate_count += 1
                if transaction.has_error:
                    error_count += 1
                    
            except Exception as e:
                transactions.append(TransactionPreview(
                    row_number=idx,
                    description="Parse Error",
                    amount=0.0,
                    currency=config.default_currency,
                    type="expense",
                    date=datetime.now(),
                    has_error=True,
                    error_message=str(e),
                    raw_data=row
                ))
                error_count += 1
        
        # Calculate statistics
        valid_rows = len([t for t in transactions if not t.has_error])
        
        # Detect date range
        valid_dates = [t.date for t in transactions if not t.has_error]
        date_range = None
        if valid_dates:
            date_range = {
                "start": min(valid_dates),
                "end": max(valid_dates)
            }
        
        preview = CSVImportPreview(
            total_rows=len(rows),
            valid_rows=valid_rows,
            duplicate_rows=duplicate_count,
            error_rows=error_count,
            transactions=transactions,
            date_range=date_range
        )
        
        return preview
    
    def _parse_row(
        self,
        row: Dict[str, str],
        row_number: int,
        config: CSVImportConfig,
        existing_transactions: List[Transaction]
    ) -> TransactionPreview:
        """Parse a single CSV row into a transaction preview"""
        
        mapping = config.field_mapping
        
        # Extract date
        date_str = row.get(mapping.date_column, "").strip()
        try:
            transaction_date = datetime.strptime(date_str, mapping.date_format)
        except ValueError:
            # Try common formats as fallback
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                try:
                    transaction_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                raise ValueError(f"Could not parse date: {date_str}")
        
        # Extract description
        description = row.get(mapping.description_column, "").strip()
        if not description:
            description = "Imported Transaction"
        
        # Extract amount (handle both single amount and debit/credit columns)
        amount = 0.0
        transaction_type = TransactionType.EXPENSE
        
        if mapping.debit_column and mapping.credit_column:
            # Handle split debit/credit columns
            debit_str = row.get(mapping.debit_column, "").strip()
            credit_str = row.get(mapping.credit_column, "").strip()
            
            debit = self._parse_amount(debit_str) if debit_str else 0.0
            credit = self._parse_amount(credit_str) if credit_str else 0.0
            
            if debit > 0:
                amount = debit
                transaction_type = TransactionType.EXPENSE
            elif credit > 0:
                amount = credit
                transaction_type = TransactionType.INCOME
            else:
                amount = 0.0
        else:
            # Handle single amount column
            amount_str = row.get(mapping.amount_column, "").strip()
            amount = self._parse_amount(amount_str)
            
            # Determine transaction type
            if mapping.type_column:
                type_value = row.get(mapping.type_column, "").strip().lower()
                transaction_type = self._infer_type_from_value(type_value, config)
            else:
                # Infer from amount sign
                if mapping.negative_means_expense:
                    transaction_type = TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
                else:
                    transaction_type = TransactionType.INCOME if amount < 0 else TransactionType.EXPENSE
                
                amount = abs(amount)
        
        # If we still don't have a type, try to infer from description
        if not mapping.type_column and config.type_inference_rules:
            inferred_type = self._infer_type_from_description(
                description, 
                config.type_inference_rules
            )
            if inferred_type:
                transaction_type = inferred_type
        
        # Extract category
        category = None
        if mapping.category_column:
            category = row.get(mapping.category_column, "").strip() or None
        
        # Extract account
        account = config.default_account
        if mapping.account_column:
            account = row.get(mapping.account_column, "").strip() or account
        
        # Extract currency
        currency = config.default_currency
        if mapping.currency_column:
            currency = row.get(mapping.currency_column, "").strip() or currency
        
        # Extract Monarch-style enhanced fields
        merchant = None
        if mapping.merchant_column:
            merchant = row.get(mapping.merchant_column, "").strip() or None
        
        original_statement = None
        if mapping.original_statement_column:
            original_statement = row.get(mapping.original_statement_column, "").strip() or None
        
        notes = None
        if mapping.notes_column:
            notes = row.get(mapping.notes_column, "").strip() or None
        
        tags = []
        if mapping.tags_column:
            tags_str = row.get(mapping.tags_column, "").strip()
            if tags_str:
                # Split by common delimiters
                tags = [t.strip() for t in tags_str.replace(';', ',').split(',') if t.strip()]
        
        # Infer investment transactions and extract ticker
        ticker = None
        if category and category.lower() in ['buy', 'sell']:
            # Change type to investment type
            transaction_type = TransactionType.BUY if category.lower() == 'buy' else TransactionType.SELL
            
            # Try to extract ticker from description or original statement
            # Monarch format often has "TICKER - Action" in original statement
            if original_statement:
                ticker = self._extract_ticker(original_statement)
            if not ticker and description:
                ticker = self._extract_ticker(description)
        
        # Check for duplicates
        is_duplicate = False
        duplicate_reason = None
        
        if config.skip_duplicates:
            is_duplicate, duplicate_reason = self._check_duplicate(
                description=description,
                amount=amount,
                date=transaction_date,
                existing_transactions=existing_transactions
            )
        
        # Apply date range filter
        has_error = False
        error_message = None
        
        if config.date_range_start and transaction_date < config.date_range_start:
            has_error = True
            error_message = f"Date {transaction_date} is before range start {config.date_range_start}"
        
        if config.date_range_end and transaction_date > config.date_range_end:
            has_error = True
            error_message = f"Date {transaction_date} is after range end {config.date_range_end}"
        
        return TransactionPreview(
            row_number=row_number,
            description=description,
            amount=abs(amount),
            currency=currency,
            type=transaction_type.value,
            category=category,
            date=transaction_date,
            account=account,
            merchant=merchant,
            original_statement=original_statement,
            notes=notes,
            tags=tags,
            ticker=ticker,
            is_duplicate=is_duplicate,
            duplicate_reason=duplicate_reason,
            has_error=has_error,
            error_message=error_message,
            raw_data=row
        )
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string to float, handling various formats"""
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and whitespace
        amount_str = amount_str.strip()
        for symbol in ['$', '€', '£', 'R$', 'C$', ',']:
            amount_str = amount_str.replace(symbol, '')
        
        # Handle parentheses as negative (accounting format)
        if amount_str.startswith('(') and amount_str.endswith(')'):
            amount_str = '-' + amount_str[1:-1]
        
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def _infer_type_from_value(self, type_value: str, config: CSVImportConfig) -> TransactionType:
        """Infer transaction type from type column value"""
        type_value = type_value.lower()
        
        # Common patterns
        if any(word in type_value for word in ['credit', 'deposit', 'payment received', 'income', 'refund']):
            return TransactionType.INCOME
        elif any(word in type_value for word in ['debit', 'withdrawal', 'payment', 'purchase', 'expense']):
            return TransactionType.EXPENSE
        elif any(word in type_value for word in ['transfer', 'xfer']):
            return TransactionType.TRANSFER
        
        return TransactionType.EXPENSE  # Default
    
    def _infer_type_from_description(
        self, 
        description: str, 
        rules: Dict[str, str]
    ) -> Optional[TransactionType]:
        """Infer transaction type from description using rules"""
        description_lower = description.lower()
        
        for keyword, type_str in rules.items():
            if keyword.lower() in description_lower:
                try:
                    return TransactionType(type_str.lower())
                except ValueError:
                    continue
        
        return None
    
    def _extract_ticker(self, text: str) -> Optional[str]:
        """Extract ticker symbol from text"""
        import re
        
        # Common patterns for tickers in Monarch exports:
        # "VTI - Limit buy" or "VTI - Sold asset" 
        # Match 2-5 uppercase letters/numbers at start, optionally with .F or .TO suffix
        match = re.match(r'^([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\s*[-:]', text)
        if match:
            return match.group(1)
        
        # Try just finding uppercase ticker at start
        match = re.match(r'^([A-Z]{2,5}(?:\.[A-Z]{1,2})?)\s', text)
        if match:
            return match.group(1)
        
        return None
    
    def _check_duplicate(
        self,
        description: str,
        amount: float,
        date: datetime,
        existing_transactions: List[Transaction]
    ) -> Tuple[bool, Optional[str]]:
        """Check if transaction is a duplicate"""
        
        # Check against existing transactions
        for tx in existing_transactions:
            # Match on date, amount, and description
            if (tx.date.date() == date.date() and 
                abs(tx.amount - amount) < 0.01 and 
                tx.description.lower() == description.lower()):
                return True, f"Matches existing transaction ID {tx.id}"
        
        return False, None
    
    def create_transactions_from_preview(
        self,
        preview: CSVImportPreview,
        skip_duplicates: bool = True,
        skip_errors: bool = True,
        selected_rows: Optional[List[int]] = None
    ) -> List[TransactionCreate]:
        """Convert preview transactions to TransactionCreate objects"""
        
        transactions = []
        
        for tx_preview in preview.transactions:
            # Skip based on filters
            if skip_duplicates and tx_preview.is_duplicate:
                continue
            if skip_errors and tx_preview.has_error:
                continue
            if selected_rows is not None and tx_preview.row_number not in selected_rows:
                continue
            
            # Create transaction
            transaction = TransactionCreate(
                description=tx_preview.description,
                amount=tx_preview.amount,
                currency=tx_preview.currency,
                type=TransactionType(tx_preview.type),
                category=tx_preview.category,
                date=tx_preview.date,
                account=tx_preview.account,
                merchant=tx_preview.merchant,
                original_statement=tx_preview.original_statement,
                notes=tx_preview.notes,
                tags=tx_preview.tags,
                ticker=tx_preview.ticker
            )
            transactions.append(transaction)
        
        return transactions

