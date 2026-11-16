from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class BankFormat(str, Enum):
    """Supported CSV import formats.

    Canopy is CAD + USD only. Historic Brazilian-brokerage formats
    (Nubank, Clear, XP, B3 CEI, Itau, Bradesco, Santander) have been
    removed from the product; Wealthsimple and Monarch are the
    recommended import paths.
    """

    GENERIC = "generic"
    MONARCH = "monarch"
    # US Banks
    CHASE = "chase"
    BANK_OF_AMERICA = "bank_of_america"
    WELLS_FARGO = "wells_fargo"
    CITIBANK = "citibank"
    CAPITAL_ONE = "capital_one"
    AMEX = "amex"
    AMEX_YEAR_END_SUMMARY = "amex_year_end_summary"
    AMEX_MONTHLY_STATEMENT_CA = "amex_monthly_statement_ca"
    DISCOVER = "discover"
    SCHWAB = "schwab"
    # Canadian Banks
    TD_BANK = "td_bank"
    RBC = "rbc"
    SCOTIABANK = "scotiabank"
    BMO = "bmo"
    WEALTHSIMPLE = "wealthsimple"
    WEALTHSIMPLE_TRADE = "wealthsimple_trade"
    # International
    WISE = "wise"
    # Custom
    CUSTOM = "custom"


class FieldMapping(BaseModel):
    """Maps CSV columns to transaction fields"""

    date_column: str
    description_column: str
    amount_column: str | None = None  # Optional if using debit/credit columns
    type_column: str | None = None  # For determining income/expense
    category_column: str | None = None
    account_column: str | None = None
    currency_column: str | None = None
    balance_column: str | None = None  # For reconciliation

    # Additional columns for better data extraction
    debit_column: str | None = None  # Some banks split debit/credit
    credit_column: str | None = None
    transaction_id_column: str | None = None  # For duplicate detection

    # Monarch-style enhanced fields
    merchant_column: str | None = None  # Clean merchant name
    original_statement_column: str | None = None  # Raw bank text
    notes_column: str | None = None  # User notes
    tags_column: str | None = None  # Tags (comma-separated or similar)

    # Investment-specific fields
    ticker_column: str | None = None
    shares_column: str | None = None
    price_column: str | None = None
    fees_column: str | None = None
    operation_column: str | None = None  # Buy/Sell/Dividend

    # Date parsing configuration
    date_format: str = "%Y-%m-%d"  # Default format

    # Amount parsing configuration
    amount_is_absolute: bool = False  # If true, use type to determine sign
    negative_means_expense: bool = True  # If false, negative means income
    decimal_separator: str = "."  # Some countries use comma


class CSVImportConfig(BaseModel):
    """Configuration for importing a CSV file"""

    bank_format: BankFormat = BankFormat.GENERIC
    field_mapping: FieldMapping
    default_currency: str = "CAD"
    default_account: str | None = None
    skip_rows: int = 0  # Number of header rows to skip
    skip_duplicates: bool = True
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None

    # Type inference rules
    type_inference_rules: dict[str, str] | None = None  # keyword -> type mapping


class TransactionPreview(BaseModel):
    """Preview of a transaction to be imported"""

    row_number: int
    description: str
    amount: float
    currency: str
    type: str
    category: str | None = None
    date: datetime
    account: str | None = None

    # Monarch-style enhanced fields
    merchant: str | None = None
    original_statement: str | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Investment fields
    ticker: str | None = None
    shares: float | None = None
    price_per_share: float | None = None
    fees: float | None = None

    is_duplicate: bool = False
    duplicate_reason: str | None = None
    has_error: bool = False
    error_message: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)  # Original CSV row


class CSVImportPreview(BaseModel):
    """Preview of entire import before committing"""

    total_rows: int
    valid_rows: int
    duplicate_rows: int
    error_rows: int
    transactions: list[TransactionPreview]
    detected_currency: str | None = None
    detected_account: str | None = None
    date_range: dict[str, datetime] | None = None


class CSVImportRequest(BaseModel):
    """Request to import transactions from preview"""

    import_id: str
    skip_duplicates: bool = True
    skip_errors: bool = True
    selected_rows: list[int] | None = None  # If None, import all valid rows


class ImportResult(BaseModel):
    """Result of import operation"""

    import_id: str
    status: ImportStatus
    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    errors: list[dict[str, Any]] = Field(default_factory=list)
    imported_transaction_ids: list[int] = Field(default_factory=list)
    duration_seconds: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)


class ImportHistory(BaseModel):
    """Historical record of an import"""

    import_id: str
    filename: str
    bank_format: BankFormat
    status: ImportStatus
    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    created_at: datetime
    completed_at: datetime | None = None
    config: CSVImportConfig | None = None


class ImportHistoryList(BaseModel):
    """List of import history records"""

    imports: list[ImportHistory]
    total: int
