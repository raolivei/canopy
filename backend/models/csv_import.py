from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"

class BankFormat(str, Enum):
    GENERIC = "generic"
    MONARCH = "monarch"
    # US Banks
    CHASE = "chase"
    BANK_OF_AMERICA = "bank_of_america"
    WELLS_FARGO = "wells_fargo"
    CITIBANK = "citibank"
    CAPITAL_ONE = "capital_one"
    AMEX = "amex"
    DISCOVER = "discover"
    SCHWAB = "schwab"
    # Canadian Banks
    TD_BANK = "td_bank"
    RBC = "rbc"
    SCOTIABANK = "scotiabank"
    BMO = "bmo"
    WEALTHSIMPLE = "wealthsimple"
    WEALTHSIMPLE_TRADE = "wealthsimple_trade"
    # Brazilian Banks
    NUBANK = "nubank"
    NUBANK_INVESTMENTS = "nubank_investments"
    CLEAR = "clear"
    CLEAR_POSITIONS = "clear_positions"
    XP = "xp"
    XP_POSITIONS = "xp_positions"
    B3_CEI = "b3_cei"
    ITAU = "itau"
    BRADESCO = "bradesco"
    SANTANDER = "santander"
    # International
    WISE = "wise"
    # Custom
    CUSTOM = "custom"

class FieldMapping(BaseModel):
    """Maps CSV columns to transaction fields"""
    date_column: str
    description_column: str
    amount_column: Optional[str] = None  # Optional if using debit/credit columns
    type_column: Optional[str] = None  # For determining income/expense
    category_column: Optional[str] = None
    account_column: Optional[str] = None
    currency_column: Optional[str] = None
    balance_column: Optional[str] = None  # For reconciliation
    
    # Additional columns for better data extraction
    debit_column: Optional[str] = None  # Some banks split debit/credit
    credit_column: Optional[str] = None
    transaction_id_column: Optional[str] = None  # For duplicate detection
    
    # Monarch-style enhanced fields
    merchant_column: Optional[str] = None  # Clean merchant name
    original_statement_column: Optional[str] = None  # Raw bank text
    notes_column: Optional[str] = None  # User notes
    tags_column: Optional[str] = None  # Tags (comma-separated or similar)
    
    # Investment-specific fields
    ticker_column: Optional[str] = None
    shares_column: Optional[str] = None
    price_column: Optional[str] = None
    fees_column: Optional[str] = None
    operation_column: Optional[str] = None  # Buy/Sell/Dividend
    
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
    default_currency: str = "USD"
    default_account: Optional[str] = None
    skip_rows: int = 0  # Number of header rows to skip
    skip_duplicates: bool = True
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    
    # Type inference rules
    type_inference_rules: Optional[Dict[str, str]] = None  # keyword -> type mapping
    
class TransactionPreview(BaseModel):
    """Preview of a transaction to be imported"""
    row_number: int
    description: str
    amount: float
    currency: str
    type: str
    category: Optional[str] = None
    date: datetime
    account: Optional[str] = None
    
    # Monarch-style enhanced fields
    merchant: Optional[str] = None
    original_statement: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Investment fields
    ticker: Optional[str] = None
    shares: Optional[float] = None
    price_per_share: Optional[float] = None
    fees: Optional[float] = None
    
    is_duplicate: bool = False
    duplicate_reason: Optional[str] = None
    has_error: bool = False
    error_message: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)  # Original CSV row

class CSVImportPreview(BaseModel):
    """Preview of entire import before committing"""
    total_rows: int
    valid_rows: int
    duplicate_rows: int
    error_rows: int
    transactions: List[TransactionPreview]
    detected_currency: Optional[str] = None
    detected_account: Optional[str] = None
    date_range: Optional[Dict[str, datetime]] = None

class CSVImportRequest(BaseModel):
    """Request to import transactions from preview"""
    import_id: str
    skip_duplicates: bool = True
    skip_errors: bool = True
    selected_rows: Optional[List[int]] = None  # If None, import all valid rows

class ImportResult(BaseModel):
    """Result of import operation"""
    import_id: str
    status: ImportStatus
    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    imported_transaction_ids: List[int] = Field(default_factory=list)
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
    completed_at: Optional[datetime] = None
    config: Optional[CSVImportConfig] = None

class ImportHistoryList(BaseModel):
    """List of import history records"""
    imports: List[ImportHistory]
    total: int
