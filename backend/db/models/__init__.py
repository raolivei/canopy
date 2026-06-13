"""SQLAlchemy ORM models for Canopy - Personal Finance Platform."""

from backend.db.models.account_balance_history import AccountBalanceHistory
from backend.db.models.asset import Asset, AssetType, SyncSource
from backend.db.models.budget import Budget, BudgetCategory, BudgetTracking, PeriodType
from backend.db.models.category import Category
from backend.db.models.dividend import Dividend, DividendType
from backend.db.models.fx_rate import FxRate
from backend.db.models.imported_event import ImportedEvent
from backend.db.models.liability import (
    Liability,
    LiabilityBalanceHistory,
    LiabilityPayment,
    LiabilityStatus,
    LiabilityType,
)
from backend.db.models.lot import Lot
from backend.db.models.portfolio_review import (
    PortfolioReview,
    PortfolioReviewLine,
    ReviewSource,
)
from backend.db.models.portfolio_snapshot import PortfolioSnapshot, SnapshotHolding
from backend.db.models.price_history import PriceHistory
from backend.db.models.real_estate import (
    PaymentFrequency,
    PaymentStatus,
    RealEstatePayment,
    RealEstatePaymentSeries,
    RealEstateProperty,
)
from backend.db.models.rule import (
    Rule,
    RuleCondition,
    RuleAction,
    RuleConditionField,
    RuleConditionOperator,
    RuleActionType,
)
from backend.db.models.transaction import Transaction, TransactionType
from backend.db.models.recurring_pattern import RecurringPattern, RecurringFrequency

__all__ = [
    # Core assets
    "Asset",
    "AssetType",
    "SyncSource",
    "Lot",
    "Dividend",
    "DividendType",
    "PriceHistory",
    "PortfolioSnapshot",
    "SnapshotHolding",
    # Real estate
    "RealEstateProperty",
    "RealEstatePaymentSeries",
    "RealEstatePayment",
    "PaymentStatus",
    "PaymentFrequency",
    # Liabilities
    "Liability",
    "LiabilityType",
    "LiabilityStatus",
    "LiabilityBalanceHistory",
    "LiabilityPayment",
    # Transactions
    "Transaction",
    "TransactionType",
    # Categories
    "Category",
    # Rules
    "Rule",
    "RuleCondition",
    "RuleAction",
    "RuleConditionField",
    "RuleConditionOperator",
    "RuleActionType",
    # Budgets
    "Budget",
    "BudgetCategory",
    "PeriodType",
    "BudgetTracking",
    # Portfolio review (CAD-only snapshots for holdings that don't auto-sync)
    "PortfolioReview",
    "PortfolioReviewLine",
    "ReviewSource",
    # CSV auto-import
    "ImportedEvent",
    "AccountBalanceHistory",
    # Foreign exchange (CAD <-> USD)
    "FxRate",
    # Recurring patterns
    "RecurringPattern",
    "RecurringFrequency",
]
