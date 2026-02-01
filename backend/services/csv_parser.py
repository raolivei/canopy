import csv
import io
import re
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
        # ==================== US Banks ====================
        BankFormat.MONARCH: FieldMapping(
            date_column="Date",
            merchant_column="Merchant",
            description_column="Merchant",
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
        BankFormat.SCHWAB: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            type_column="Action",
            ticker_column="Symbol",
            shares_column="Quantity",
            price_column="Price",
            fees_column="Fees & Comm",
            date_format="%m/%d/%Y",
            negative_means_expense=True
        ),
        
        # ==================== Canadian Banks ====================
        BankFormat.TD_BANK: FieldMapping(
            date_column="Date",
            description_column="Description",
            debit_column="Debit",
            credit_column="Credit",
            date_format="%m/%d/%Y"
        ),
        BankFormat.RBC: FieldMapping(
            date_column="Transaction Date",
            description_column="Description 1",
            debit_column="CAD$",
            credit_column="CAD$",
            account_column="Account Number",
            date_format="%m/%d/%Y"
        ),
        BankFormat.WEALTHSIMPLE: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            account_column="Account",
            currency_column="Currency",
            date_format="%Y-%m-%d",
            negative_means_expense=True
        ),
        BankFormat.WEALTHSIMPLE_TRADE: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Market Value",
            operation_column="Transaction Type",
            ticker_column="Symbol",
            shares_column="Quantity",
            price_column="Price",
            currency_column="Currency",
            account_column="Account",
            date_format="%Y-%m-%d"
        ),
        
        # ==================== Brazilian Banks ====================
        BankFormat.NUBANK: FieldMapping(
            date_column="date",
            description_column="title",
            amount_column="amount",
            category_column="category",
            date_format="%Y-%m-%d",
            negative_means_expense=False,
            decimal_separator="."
        ),
        BankFormat.NUBANK_INVESTMENTS: FieldMapping(
            date_column="Data",
            description_column="Descrição",
            amount_column="Valor",
            operation_column="Tipo",
            ticker_column="Ativo",
            shares_column="Quantidade",
            price_column="Preço",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        BankFormat.CLEAR: FieldMapping(
            date_column="Data Negócio",
            description_column="Especificação do Título",
            amount_column="Valor Total",
            operation_column="C/V",  # C = Compra, V = Venda
            ticker_column="Código",
            shares_column="Quantidade",
            price_column="Preço",
            fees_column="Taxa",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        BankFormat.CLEAR_POSITIONS: FieldMapping(
            date_column="Data",
            description_column="Produto",
            amount_column="Valor Atualizado",
            ticker_column="Código",
            shares_column="Quantidade",
            price_column="Preço Médio",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        BankFormat.XP: FieldMapping(
            date_column="Data do Negócio",
            description_column="Especificação do Ativo",
            amount_column="Valor Líquido",
            operation_column="Tipo de Movimentação",  # Compra/Venda
            ticker_column="Código do Ativo",
            shares_column="Quantidade",
            price_column="Preço Unitário",
            fees_column="Taxas",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        BankFormat.XP_POSITIONS: FieldMapping(
            date_column="Data Posição",
            description_column="Produto",
            amount_column="Valor Bruto",
            ticker_column="Código",
            shares_column="Quantidade",
            price_column="Preço Médio",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        BankFormat.B3_CEI: FieldMapping(
            date_column="Data do Negócio",
            description_column="Especificação do título",
            amount_column="Valor",
            operation_column="Tipo de Movimentação",
            ticker_column="Código de Negociação",
            shares_column="Quantidade",
            price_column="Preço",
            account_column="Instituição",
            date_format="%d/%m/%Y",
            decimal_separator=","
        ),
        
        # ==================== International ====================
        BankFormat.WISE: FieldMapping(
            date_column="Date",
            description_column="Description",
            amount_column="Amount",
            currency_column="Currency",
            type_column="TransferWise ID",  # Used to detect type
            transaction_id_column="TransferWise ID",
            balance_column="Running Balance",
            date_format="%Y-%m-%d",
            negative_means_expense=True
        ),
    }
    
    # Brazilian format detection patterns
    BRAZILIAN_HEADER_PATTERNS = {
        BankFormat.CLEAR: ["data negócio", "c/v", "código", "especificação"],
        BankFormat.XP: ["data do negócio", "código do ativo", "tipo de movimentação"],
        BankFormat.B3_CEI: ["código de negociação", "instituição", "data do negócio"],
        BankFormat.NUBANK_INVESTMENTS: ["ativo", "quantidade", "preço", "tipo"],
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
        
        # Wise detection
        if "transferwise id" in headers_lower or ("date" in headers_lower and "running balance" in headers_lower and "currency" in headers_lower):
            return BankFormat.WISE
        
        # Wealthsimple Trade detection
        if "symbol" in headers_lower and "transaction type" in headers_lower and "market value" in headers_lower:
            return BankFormat.WEALTHSIMPLE_TRADE
        
        # Wealthsimple Cash detection
        if "date" in headers_lower and "description" in headers_lower and "currency" in headers_lower and "amount" in headers_lower:
            return BankFormat.WEALTHSIMPLE
        
        # Schwab detection
        if "action" in headers_lower and "symbol" in headers_lower and "fees & comm" in headers_lower:
            return BankFormat.SCHWAB
        
        # Chase detection
        if "posting date" in headers_lower and "type" in headers_lower:
            return BankFormat.CHASE
            
        # Capital One detection
        if "transaction date" in headers_lower and "debit" in headers_lower:
            return BankFormat.CAPITAL_ONE
        
        # RBC detection
        if "account number" in headers_lower and ("description 1" in headers_lower or "transaction date" in headers_lower):
            return BankFormat.RBC
        
        # Brazilian brokerages - check for Portuguese headers
        headers_joined = " ".join(headers_lower)
        
        for format_type, patterns in self.BRAZILIAN_HEADER_PATTERNS.items():
            if all(pattern in headers_joined for pattern in patterns):
                return format_type
        
        # Nubank detection
        if "date" in headers_lower and "title" in headers_lower and "category" in headers_lower:
            return BankFormat.NUBANK
            
        # Clear positions (simpler check)
        if "código" in headers_lower and "quantidade" in headers_lower and "preço médio" in headers_lower:
            return BankFormat.CLEAR_POSITIONS
        
        # XP positions
        if "código" in headers_lower and "quantidade" in headers_lower and "produto" in headers_lower:
            return BankFormat.XP_POSITIONS
            
        return None
    
    def _parse_brazilian_amount(self, amount_str: str) -> float:
        """Parse Brazilian number format (1.234,56 -> 1234.56)"""
        if not amount_str:
            return 0.0
        
        # Remove currency symbols and whitespace
        amount_str = amount_str.strip()
        for symbol in ['R$', 'BRL', ' ']:
            amount_str = amount_str.replace(symbol, '')
        
        # Handle parentheses as negative
        is_negative = False
        if amount_str.startswith('(') and amount_str.endswith(')'):
            is_negative = True
            amount_str = amount_str[1:-1]
        if amount_str.startswith('-'):
            is_negative = True
            amount_str = amount_str[1:]
        
        # Brazilian format: 1.234,56 -> 1234.56
        # Remove thousand separators (.)
        amount_str = amount_str.replace('.', '')
        # Convert decimal separator (, -> .)
        amount_str = amount_str.replace(',', '.')
        
        try:
            result = float(amount_str)
            return -result if is_negative else result
        except ValueError:
            return 0.0
        
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
        is_brazilian = config.bank_format in [
            BankFormat.NUBANK, BankFormat.NUBANK_INVESTMENTS,
            BankFormat.CLEAR, BankFormat.CLEAR_POSITIONS,
            BankFormat.XP, BankFormat.XP_POSITIONS, BankFormat.B3_CEI
        ]
        
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
            
            if is_brazilian:
                debit = self._parse_brazilian_amount(debit_str) if debit_str else 0.0
                credit = self._parse_brazilian_amount(credit_str) if credit_str else 0.0
            else:
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
            if is_brazilian:
                amount = self._parse_brazilian_amount(amount_str)
            else:
                amount = self._parse_amount(amount_str)
            
            # Determine transaction type from operation column (for investment transactions)
            if mapping.operation_column:
                op_value = row.get(mapping.operation_column, "").strip().lower()
                if op_value in ['c', 'compra', 'buy', 'bought', 'deposit', 'contribution']:
                    transaction_type = TransactionType.BUY
                elif op_value in ['v', 'venda', 'sell', 'sold', 'withdrawal']:
                    transaction_type = TransactionType.SELL
                elif op_value in ['dividendo', 'dividend', 'jcp', 'rendimento']:
                    transaction_type = TransactionType.INCOME
                elif op_value in ['transfer', 'transferência']:
                    transaction_type = TransactionType.TRANSFER
            elif mapping.type_column:
                type_value = row.get(mapping.type_column, "").strip().lower()
                transaction_type = self._infer_type_from_value(type_value, config)
            else:
                # Infer from amount sign
                if mapping.negative_means_expense:
                    transaction_type = TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME
                else:
                    transaction_type = TransactionType.INCOME if amount < 0 else TransactionType.EXPENSE
                
                amount = abs(amount)
        
        # Extract ticker and investment fields
        ticker = None
        shares = None
        price_per_share = None
        fees = None
        
        if mapping.ticker_column:
            ticker = row.get(mapping.ticker_column, "").strip().upper() or None
        
        if mapping.shares_column:
            shares_str = row.get(mapping.shares_column, "").strip()
            if shares_str:
                if is_brazilian:
                    shares = self._parse_brazilian_amount(shares_str)
                else:
                    shares = self._parse_amount(shares_str)
        
        if mapping.price_column:
            price_str = row.get(mapping.price_column, "").strip()
            if price_str:
                if is_brazilian:
                    price_per_share = self._parse_brazilian_amount(price_str)
                else:
                    price_per_share = self._parse_amount(price_str)
        
        if mapping.fees_column:
            fees_str = row.get(mapping.fees_column, "").strip()
            if fees_str:
                if is_brazilian:
                    fees = abs(self._parse_brazilian_amount(fees_str))
                else:
                    fees = abs(self._parse_amount(fees_str))
        
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
                tags = [t.strip() for t in tags_str.replace(';', ',').split(',') if t.strip()]
        
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
            shares=shares,
            price_per_share=price_per_share,
            fees=fees,
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
        for symbol in ['$', '€', '£', 'R$', 'C$', 'CAD', 'USD', 'BRL', ' ']:
            amount_str = amount_str.replace(symbol, '')
        
        # Remove thousand separators (comma in US format)
        amount_str = amount_str.replace(',', '')
        
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
        
        # Investment patterns
        if any(word in type_value for word in ['buy', 'bought', 'purchase', 'compra']):
            return TransactionType.BUY
        elif any(word in type_value for word in ['sell', 'sold', 'venda']):
            return TransactionType.SELL
        
        # Common patterns
        if any(word in type_value for word in ['credit', 'deposit', 'payment received', 'income', 'refund', 'dividend']):
            return TransactionType.INCOME
        elif any(word in type_value for word in ['debit', 'withdrawal', 'payment', 'purchase', 'expense']):
            return TransactionType.EXPENSE
        elif any(word in type_value for word in ['transfer', 'xfer']):
            return TransactionType.TRANSFER
        
        return TransactionType.EXPENSE  # Default
    
    def _check_duplicate(
        self,
        description: str,
        amount: float,
        date: datetime,
        existing_transactions: List[Transaction]
    ) -> Tuple[bool, Optional[str]]:
        """Check if transaction is a duplicate"""
        
        for tx in existing_transactions:
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
            if skip_duplicates and tx_preview.is_duplicate:
                continue
            if skip_errors and tx_preview.has_error:
                continue
            if selected_rows is not None and tx_preview.row_number not in selected_rows:
                continue
            
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
                ticker=tx_preview.ticker,
                shares=tx_preview.shares,
                price_per_share=tx_preview.price_per_share
            )
            transactions.append(transaction)
        
        return transactions
