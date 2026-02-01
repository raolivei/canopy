"""Insights calculator for portfolio analytics.

Canopy - Personal Finance Platform

Provides:
- Net worth calculation (multi-currency with USD base)
- Asset allocation by type, currency, country
- Growth rate calculations (monthly, yearly)
- Currency exposure analysis
- Passive income tracking
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from dataclasses import dataclass, field

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db.models import (
    Asset,
    AssetType,
    Lot,
    PortfolioSnapshot,
    SnapshotHolding,
    Liability,
    RealEstateProperty,
)


# Default exchange rates (will be fetched dynamically in production)
DEFAULT_EXCHANGE_RATES = {
    "USD": Decimal("1.0"),
    "CAD": Decimal("0.74"),  # 1 CAD = 0.74 USD
    "BRL": Decimal("0.17"),  # 1 BRL = 0.17 USD
    "EUR": Decimal("1.08"),  # 1 EUR = 1.08 USD
    "BTC": Decimal("97000"),  # 1 BTC = ~$97,000 USD
    "ETH": Decimal("3400"),   # 1 ETH = ~$3,400 USD
}


@dataclass
class CurrencyAmount:
    """Amount with currency information."""
    amount: Decimal
    currency: str
    amount_usd: Decimal = Decimal("0")
    
    def __post_init__(self):
        if self.amount_usd == Decimal("0") and self.currency in DEFAULT_EXCHANGE_RATES:
            self.amount_usd = self.amount * DEFAULT_EXCHANGE_RATES[self.currency]


@dataclass
class NetWorthSummary:
    """Summary of net worth across all currencies."""
    total_assets_usd: Decimal = Decimal("0")
    total_liabilities_usd: Decimal = Decimal("0")
    net_worth_usd: Decimal = Decimal("0")
    
    # By currency
    assets_by_currency: dict[str, Decimal] = field(default_factory=dict)
    liabilities_by_currency: dict[str, Decimal] = field(default_factory=dict)
    
    # Components
    liquid_assets_usd: Decimal = Decimal("0")  # Cash, bank accounts
    investment_assets_usd: Decimal = Decimal("0")  # Stocks, ETFs, crypto
    retirement_assets_usd: Decimal = Decimal("0")  # RRSP, TFSA, etc.
    real_estate_equity_usd: Decimal = Decimal("0")  # Property equity
    
    # Change tracking
    change_1d: Optional[Decimal] = None
    change_1d_percent: Optional[Decimal] = None
    change_1m: Optional[Decimal] = None
    change_1m_percent: Optional[Decimal] = None
    change_ytd: Optional[Decimal] = None
    change_ytd_percent: Optional[Decimal] = None


@dataclass
class AllocationBreakdown:
    """Asset allocation breakdown."""
    by_type: dict[str, Decimal] = field(default_factory=dict)  # stock: 35%, crypto: 20%, etc.
    by_currency: dict[str, Decimal] = field(default_factory=dict)  # CAD: 45%, USD: 35%, etc.
    by_country: dict[str, Decimal] = field(default_factory=dict)  # CA: 50%, US: 30%, BR: 20%
    by_institution: dict[str, Decimal] = field(default_factory=dict)  # Wealthsimple: 40%, etc.


@dataclass
class GrowthMetrics:
    """Portfolio growth metrics."""
    monthly_growth_rate: Decimal = Decimal("0")
    yearly_growth_rate: Decimal = Decimal("0")
    average_monthly_growth: Decimal = Decimal("0")
    best_month: Optional[date] = None
    best_month_return: Optional[Decimal] = None
    worst_month: Optional[date] = None
    worst_month_return: Optional[Decimal] = None


@dataclass 
class CurrencyExposure:
    """Currency exposure analysis."""
    exposures: dict[str, Decimal] = field(default_factory=dict)  # Currency -> percentage
    amounts_usd: dict[str, Decimal] = field(default_factory=dict)  # Currency -> amount in USD
    risk_assessment: str = "balanced"  # "concentrated", "balanced", "diversified"


class InsightsCalculator:
    """Calculator for portfolio insights and analytics."""
    
    def __init__(
        self, 
        db: Session, 
        exchange_rates: Optional[dict[str, Decimal]] = None,
        base_currency: str = "USD"
    ):
        self.db = db
        self.exchange_rates = exchange_rates or DEFAULT_EXCHANGE_RATES
        self.base_currency = base_currency
    
    def convert_to_usd(self, amount: Decimal, currency: str) -> Decimal:
        """Convert an amount to USD."""
        if currency == "USD":
            return amount
        rate = self.exchange_rates.get(currency, Decimal("1"))
        return amount * rate
    
    def convert_from_usd(self, amount_usd: Decimal, target_currency: str) -> Decimal:
        """Convert USD to target currency."""
        if target_currency == "USD":
            return amount_usd
        rate = self.exchange_rates.get(target_currency, Decimal("1"))
        if rate == 0:
            return Decimal("0")
        return amount_usd / rate
    
    def calculate_net_worth(self) -> NetWorthSummary:
        """Calculate total net worth across all assets and liabilities."""
        summary = NetWorthSummary()
        
        # Get all assets
        assets = self.db.query(Asset).filter(Asset.is_liability == False).all()
        
        for asset in assets:
            if asset.current_price is None:
                continue
                
            # Apply ownership percentage
            value = asset.current_price * asset.ownership_percentage
            value_usd = self.convert_to_usd(value, asset.currency)
            
            # Add to totals
            summary.total_assets_usd += value_usd
            
            # Track by currency
            if asset.currency not in summary.assets_by_currency:
                summary.assets_by_currency[asset.currency] = Decimal("0")
            summary.assets_by_currency[asset.currency] += value
            
            # Categorize by type
            if asset.is_bank_account or asset.asset_type == AssetType.CASH:
                summary.liquid_assets_usd += value_usd
            elif asset.is_retirement_account:
                summary.retirement_assets_usd += value_usd
            else:
                summary.investment_assets_usd += value_usd
        
        # Get all liabilities
        liabilities = self.db.query(Liability).filter(
            Liability.status == "active"
        ).all()
        
        for liability in liabilities:
            value_usd = self.convert_to_usd(liability.current_balance, liability.currency)
            summary.total_liabilities_usd += value_usd
            
            if liability.currency not in summary.liabilities_by_currency:
                summary.liabilities_by_currency[liability.currency] = Decimal("0")
            summary.liabilities_by_currency[liability.currency] += liability.current_balance
        
        # Get real estate equity
        properties = self.db.query(RealEstateProperty).all()
        for prop in properties:
            # Use estimated market value if available, otherwise use paid amount
            if prop.estimated_market_value:
                equity = prop.user_market_value or Decimal("0")
            else:
                equity = prop.total_paid
            summary.real_estate_equity_usd += self.convert_to_usd(equity, prop.currency)
        
        # Add real estate to total assets
        summary.total_assets_usd += summary.real_estate_equity_usd
        
        # Calculate net worth
        summary.net_worth_usd = summary.total_assets_usd - summary.total_liabilities_usd
        
        # Calculate changes from historical data
        self._calculate_changes(summary)
        
        return summary
    
    def _calculate_changes(self, summary: NetWorthSummary) -> None:
        """Calculate net worth changes over different periods."""
        today = date.today()
        
        # Get historical snapshots
        snapshots = self.db.query(PortfolioSnapshot).order_by(
            PortfolioSnapshot.snapshot_date.desc()
        ).limit(365).all()
        
        if not snapshots:
            return
        
        # Find comparison points
        one_day_ago = today - timedelta(days=1)
        one_month_ago = today - timedelta(days=30)
        year_start = date(today.year, 1, 1)
        
        for snapshot in snapshots:
            snapshot_date = snapshot.snapshot_date
            
            if summary.change_1d is None and snapshot_date <= one_day_ago:
                summary.change_1d = summary.net_worth_usd - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_1d_percent = (summary.change_1d / snapshot.total_value) * 100
            
            if summary.change_1m is None and snapshot_date <= one_month_ago:
                summary.change_1m = summary.net_worth_usd - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_1m_percent = (summary.change_1m / snapshot.total_value) * 100
            
            if summary.change_ytd is None and snapshot_date <= year_start:
                summary.change_ytd = summary.net_worth_usd - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_ytd_percent = (summary.change_ytd / snapshot.total_value) * 100
    
    def calculate_allocation(self) -> AllocationBreakdown:
        """Calculate asset allocation breakdown."""
        allocation = AllocationBreakdown()
        
        # Get all non-liability assets
        assets = self.db.query(Asset).filter(Asset.is_liability == False).all()
        
        total_usd = Decimal("0")
        type_totals: dict[str, Decimal] = {}
        currency_totals: dict[str, Decimal] = {}
        country_totals: dict[str, Decimal] = {}
        institution_totals: dict[str, Decimal] = {}
        
        for asset in assets:
            if asset.current_price is None:
                continue
            
            value = asset.current_price * asset.ownership_percentage
            value_usd = self.convert_to_usd(value, asset.currency)
            total_usd += value_usd
            
            # By type
            asset_type = asset.asset_type.value
            # Simplify retirement account types
            if asset_type.startswith("retirement_"):
                asset_type = "retirement"
            elif asset_type.startswith("bank_"):
                asset_type = "cash"
            elif asset_type.startswith("liability_"):
                continue  # Skip liabilities
            
            type_totals[asset_type] = type_totals.get(asset_type, Decimal("0")) + value_usd
            
            # By currency
            currency_totals[asset.currency] = currency_totals.get(asset.currency, Decimal("0")) + value_usd
            
            # By country
            country = asset.country or "Other"
            country_totals[country] = country_totals.get(country, Decimal("0")) + value_usd
            
            # By institution
            institution = asset.institution or "Other"
            institution_totals[institution] = institution_totals.get(institution, Decimal("0")) + value_usd
        
        # Convert to percentages
        if total_usd > 0:
            allocation.by_type = {k: (v / total_usd) * 100 for k, v in type_totals.items()}
            allocation.by_currency = {k: (v / total_usd) * 100 for k, v in currency_totals.items()}
            allocation.by_country = {k: (v / total_usd) * 100 for k, v in country_totals.items()}
            allocation.by_institution = {k: (v / total_usd) * 100 for k, v in institution_totals.items()}
        
        return allocation
    
    def calculate_currency_exposure(self) -> CurrencyExposure:
        """Calculate currency exposure analysis."""
        exposure = CurrencyExposure()
        
        # Get all assets
        assets = self.db.query(Asset).filter(Asset.is_liability == False).all()
        
        total_usd = Decimal("0")
        currency_amounts: dict[str, Decimal] = {}
        
        for asset in assets:
            if asset.current_price is None:
                continue
            
            value = asset.current_price * asset.ownership_percentage
            value_usd = self.convert_to_usd(value, asset.currency)
            total_usd += value_usd
            
            # Group crypto currencies
            currency = asset.currency
            if currency in ["BTC", "ETH"]:
                currency = "Crypto"
            
            currency_amounts[currency] = currency_amounts.get(currency, Decimal("0")) + value_usd
        
        # Calculate percentages
        if total_usd > 0:
            exposure.exposures = {k: (v / total_usd) * 100 for k, v in currency_amounts.items()}
        exposure.amounts_usd = currency_amounts
        
        # Assess risk based on concentration
        max_exposure = max(exposure.exposures.values()) if exposure.exposures else 0
        if max_exposure > 70:
            exposure.risk_assessment = "concentrated"
        elif max_exposure > 50:
            exposure.risk_assessment = "balanced"
        else:
            exposure.risk_assessment = "diversified"
        
        return exposure
    
    def calculate_growth_metrics(self) -> GrowthMetrics:
        """Calculate portfolio growth metrics."""
        metrics = GrowthMetrics()
        
        # Get historical snapshots
        snapshots = self.db.query(PortfolioSnapshot).order_by(
            PortfolioSnapshot.snapshot_date.asc()
        ).all()
        
        if len(snapshots) < 2:
            return metrics
        
        # Calculate monthly returns
        monthly_returns: list[tuple[date, Decimal]] = []
        
        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            
            if prev.total_value > 0:
                return_pct = ((curr.total_value - prev.total_value) / prev.total_value) * 100
                monthly_returns.append((curr.snapshot_date, return_pct))
        
        if monthly_returns:
            # Average monthly growth
            metrics.average_monthly_growth = sum(r[1] for r in monthly_returns) / len(monthly_returns)
            
            # Best and worst months
            best = max(monthly_returns, key=lambda x: x[1])
            worst = min(monthly_returns, key=lambda x: x[1])
            
            metrics.best_month = best[0]
            metrics.best_month_return = best[1]
            metrics.worst_month = worst[0]
            metrics.worst_month_return = worst[1]
        
        # Calculate overall growth rates
        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        
        if first_snapshot.total_value > 0:
            total_return = (last_snapshot.total_value - first_snapshot.total_value) / first_snapshot.total_value
            
            # Time period in years
            days = (last_snapshot.snapshot_date - first_snapshot.snapshot_date).days
            years = days / 365.25
            
            if years > 0:
                # Annualized return
                metrics.yearly_growth_rate = ((1 + total_return) ** (1 / years) - 1) * 100
                
                # Monthly (simplified)
                months = days / 30.44
                if months > 0:
                    metrics.monthly_growth_rate = ((1 + total_return) ** (1 / months) - 1) * 100
        
        return metrics
    
    def get_historical_net_worth(
        self, 
        period: str = "1y"
    ) -> list[dict]:
        """Get historical net worth data for charting.
        
        Args:
            period: Time period - "7d", "30d", "90d", "1y", "all"
        
        Returns:
            List of {date, net_worth, assets, liabilities} dicts
        """
        today = date.today()
        
        # Determine start date based on period
        period_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "1y": 365,
            "all": 3650,  # ~10 years
        }
        days = period_days.get(period, 365)
        start_date = today - timedelta(days=days)
        
        # Get snapshots
        snapshots = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.snapshot_date >= start_date
        ).order_by(PortfolioSnapshot.snapshot_date.asc()).all()
        
        result = []
        for snapshot in snapshots:
            result.append({
                "date": snapshot.snapshot_date.isoformat(),
                "net_worth": float(snapshot.total_value),
                "cost_basis": float(snapshot.total_cost_basis),
            })
        
        return result


def get_insights_summary(db: Session, base_currency: str = "USD") -> dict:
    """Get a complete insights summary for the dashboard.
    
    Returns all key metrics in a single call for efficiency.
    """
    calculator = InsightsCalculator(db, base_currency=base_currency)
    
    net_worth = calculator.calculate_net_worth()
    allocation = calculator.calculate_allocation()
    currency_exposure = calculator.calculate_currency_exposure()
    growth = calculator.calculate_growth_metrics()
    
    return {
        "net_worth": {
            "total_usd": float(net_worth.net_worth_usd),
            "total_assets_usd": float(net_worth.total_assets_usd),
            "total_liabilities_usd": float(net_worth.total_liabilities_usd),
            "liquid_assets_usd": float(net_worth.liquid_assets_usd),
            "investment_assets_usd": float(net_worth.investment_assets_usd),
            "retirement_assets_usd": float(net_worth.retirement_assets_usd),
            "real_estate_equity_usd": float(net_worth.real_estate_equity_usd),
            "assets_by_currency": {k: float(v) for k, v in net_worth.assets_by_currency.items()},
            "liabilities_by_currency": {k: float(v) for k, v in net_worth.liabilities_by_currency.items()},
            "change_1d": float(net_worth.change_1d) if net_worth.change_1d else None,
            "change_1d_percent": float(net_worth.change_1d_percent) if net_worth.change_1d_percent else None,
            "change_1m": float(net_worth.change_1m) if net_worth.change_1m else None,
            "change_1m_percent": float(net_worth.change_1m_percent) if net_worth.change_1m_percent else None,
            "change_ytd": float(net_worth.change_ytd) if net_worth.change_ytd else None,
            "change_ytd_percent": float(net_worth.change_ytd_percent) if net_worth.change_ytd_percent else None,
        },
        "allocation": {
            "by_type": {k: float(v) for k, v in allocation.by_type.items()},
            "by_currency": {k: float(v) for k, v in allocation.by_currency.items()},
            "by_country": {k: float(v) for k, v in allocation.by_country.items()},
            "by_institution": {k: float(v) for k, v in allocation.by_institution.items()},
        },
        "currency_exposure": {
            "exposures": {k: float(v) for k, v in currency_exposure.exposures.items()},
            "amounts_usd": {k: float(v) for k, v in currency_exposure.amounts_usd.items()},
            "risk_assessment": currency_exposure.risk_assessment,
        },
        "growth": {
            "monthly_rate": float(growth.monthly_growth_rate),
            "yearly_rate": float(growth.yearly_growth_rate),
            "average_monthly": float(growth.average_monthly_growth),
            "best_month": growth.best_month.isoformat() if growth.best_month else None,
            "best_month_return": float(growth.best_month_return) if growth.best_month_return else None,
            "worst_month": growth.worst_month.isoformat() if growth.worst_month else None,
            "worst_month_return": float(growth.worst_month_return) if growth.worst_month_return else None,
        },
    }
