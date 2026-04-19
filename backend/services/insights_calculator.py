"""Insights calculator for Canadian (CAD-only) portfolios.

Canopy - Personal Finance Platform

Provides:
- Net worth calculation (CAD)
- Asset allocation by type, country, institution
- Growth rate calculations (monthly, yearly)
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from backend.db.models import (
    Asset,
    AssetType,
    Liability,
    PortfolioSnapshot,
    RealEstateProperty,
)
from backend.services.fx import convert, get_latest_rate
from backend.services.portfolio_calculator import (
    BALANCE_BASED_ASSET_TYPES,
    PortfolioCalculator,
)
from sqlalchemy.orm import Session


@dataclass
class NetWorthSummary:
    """Summary of net worth (CAD)."""

    total_assets_cad: Decimal = Decimal("0")
    total_liabilities_cad: Decimal = Decimal("0")
    net_worth_cad: Decimal = Decimal("0")

    # Components
    liquid_assets_cad: Decimal = Decimal("0")
    investment_assets_cad: Decimal = Decimal("0")
    retirement_assets_cad: Decimal = Decimal("0")
    real_estate_equity_cad: Decimal = Decimal("0")

    # Change tracking
    change_1d: Optional[Decimal] = None
    change_1d_percent: Optional[Decimal] = None
    change_1m: Optional[Decimal] = None
    change_1m_percent: Optional[Decimal] = None
    change_ytd: Optional[Decimal] = None
    change_ytd_percent: Optional[Decimal] = None


@dataclass
class AllocationBreakdown:
    """Asset allocation breakdown (percentages)."""

    by_type: dict[str, Decimal] = field(default_factory=dict)
    by_country: dict[str, Decimal] = field(default_factory=dict)
    by_institution: dict[str, Decimal] = field(default_factory=dict)


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


class InsightsCalculator:
    """Calculator for Canadian portfolio insights and analytics (CAD)."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _holding_value_cad(
        amount: Decimal,
        currency: str,
        usd_cad: Decimal,
    ) -> Decimal:
        """Convert a holding amount to CAD for roll-ups (CAD/USD only)."""
        ccy = (currency or "CAD").strip().upper() or "CAD"
        if ccy == "CAD":
            return amount
        if ccy == "USD":
            return convert(amount, from_ccy="USD", to_ccy="CAD", usd_cad_rate=usd_cad)
        return amount

    def calculate_net_worth(self) -> NetWorthSummary:
        """Calculate total CAD net worth across all assets and liabilities."""
        summary = NetWorthSummary()

        assets = self.db.query(Asset).filter(Asset.is_liability.is_(False)).all()
        calc = PortfolioCalculator(self.db)
        balance_ids = [a.id for a in assets if a.asset_type in BALANCE_BASED_ASSET_TYPES]
        balance_map = calc.native_balances_from_history(balance_ids)

        rate_row = get_latest_rate(self.db)
        usd_cad = (
            Decimal(str(rate_row.rate))
            if rate_row is not None and rate_row.rate and rate_row.rate > 0
            else Decimal("1.35")
        )

        for asset in assets:
            h = calc.get_holding_summary(asset, balance_map=balance_map)
            if h.total_shares <= 0 and (h.market_value is None or h.market_value <= 0):
                continue
            if h.market_value is None:
                continue

            mv_native = h.market_value * asset.ownership_percentage
            value = self._holding_value_cad(mv_native, h.currency, usd_cad)
            summary.total_assets_cad += value

            if asset.is_bank_account or asset.asset_type == AssetType.CASH:
                summary.liquid_assets_cad += value
            elif asset.is_retirement_account:
                summary.retirement_assets_cad += value
            else:
                summary.investment_assets_cad += value

        liabilities = self.db.query(Liability).filter(Liability.status == "active").all()
        for liability in liabilities:
            summary.total_liabilities_cad += liability.current_balance

        properties = self.db.query(RealEstateProperty).all()
        for prop in properties:
            if prop.estimated_market_value:
                equity = prop.user_market_value or Decimal("0")
            else:
                equity = prop.total_paid
            summary.real_estate_equity_cad += equity

        summary.total_assets_cad += summary.real_estate_equity_cad
        summary.net_worth_cad = summary.total_assets_cad - summary.total_liabilities_cad

        self._calculate_changes(summary)
        return summary

    def _calculate_changes(self, summary: NetWorthSummary) -> None:
        """Calculate net worth changes over different periods."""
        today = date.today()

        snapshots = (
            self.db.query(PortfolioSnapshot)
            .order_by(PortfolioSnapshot.snapshot_date.desc())
            .limit(365)
            .all()
        )
        if not snapshots:
            return

        one_day_ago = today - timedelta(days=1)
        one_month_ago = today - timedelta(days=30)
        year_start = date(today.year, 1, 1)

        for snapshot in snapshots:
            sd = snapshot.snapshot_date
            if summary.change_1d is None and sd <= one_day_ago:
                summary.change_1d = summary.net_worth_cad - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_1d_percent = (
                        summary.change_1d / snapshot.total_value
                    ) * 100
            if summary.change_1m is None and sd <= one_month_ago:
                summary.change_1m = summary.net_worth_cad - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_1m_percent = (
                        summary.change_1m / snapshot.total_value
                    ) * 100
            if summary.change_ytd is None and sd <= year_start:
                summary.change_ytd = summary.net_worth_cad - snapshot.total_value
                if snapshot.total_value > 0:
                    summary.change_ytd_percent = (
                        summary.change_ytd / snapshot.total_value
                    ) * 100

    def calculate_allocation(self) -> AllocationBreakdown:
        """Calculate asset allocation breakdown (CAD-based percentages)."""
        allocation = AllocationBreakdown()
        assets = self.db.query(Asset).filter(Asset.is_liability.is_(False)).all()
        calc = PortfolioCalculator(self.db)
        balance_ids = [a.id for a in assets if a.asset_type in BALANCE_BASED_ASSET_TYPES]
        balance_map = calc.native_balances_from_history(balance_ids)

        rate_row = get_latest_rate(self.db)
        usd_cad = (
            Decimal(str(rate_row.rate))
            if rate_row is not None and rate_row.rate and rate_row.rate > 0
            else Decimal("1.35")
        )

        total_cad = Decimal("0")
        type_totals: dict[str, Decimal] = {}
        country_totals: dict[str, Decimal] = {}
        institution_totals: dict[str, Decimal] = {}

        for asset in assets:
            h = calc.get_holding_summary(asset, balance_map=balance_map)
            if h.total_shares <= 0 and (h.market_value is None or h.market_value <= 0):
                continue
            if h.market_value is None:
                continue

            mv_native = h.market_value * asset.ownership_percentage
            value = self._holding_value_cad(mv_native, h.currency, usd_cad)
            total_cad += value

            asset_type = asset.asset_type.value
            if asset_type.startswith("retirement_"):
                asset_type = "retirement"
            elif asset_type.startswith("bank_"):
                asset_type = "cash"
            elif asset_type.startswith("liability_"):
                continue

            type_totals[asset_type] = type_totals.get(asset_type, Decimal("0")) + value

            country = asset.country or "CA"
            country_totals[country] = country_totals.get(country, Decimal("0")) + value

            institution = asset.institution or "Other"
            institution_totals[institution] = (
                institution_totals.get(institution, Decimal("0")) + value
            )

        if total_cad > 0:
            allocation.by_type = {
                k: (v / total_cad) * 100 for k, v in type_totals.items()
            }
            allocation.by_country = {
                k: (v / total_cad) * 100 for k, v in country_totals.items()
            }
            allocation.by_institution = {
                k: (v / total_cad) * 100 for k, v in institution_totals.items()
            }

        return allocation

    def calculate_growth_metrics(self) -> GrowthMetrics:
        """Calculate portfolio growth metrics from historical snapshots."""
        metrics = GrowthMetrics()
        snapshots = (
            self.db.query(PortfolioSnapshot)
            .order_by(PortfolioSnapshot.snapshot_date.asc())
            .all()
        )

        if len(snapshots) < 2:
            return metrics

        monthly_returns: list[tuple[date, Decimal]] = []
        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            if prev.total_value > 0:
                return_pct = (
                    (curr.total_value - prev.total_value) / prev.total_value
                ) * 100
                monthly_returns.append((curr.snapshot_date, return_pct))

        if monthly_returns:
            metrics.average_monthly_growth = sum(
                r[1] for r in monthly_returns
            ) / len(monthly_returns)
            best = max(monthly_returns, key=lambda x: x[1])
            worst = min(monthly_returns, key=lambda x: x[1])
            metrics.best_month = best[0]
            metrics.best_month_return = best[1]
            metrics.worst_month = worst[0]
            metrics.worst_month_return = worst[1]

        first_snapshot = snapshots[0]
        last_snapshot = snapshots[-1]
        if first_snapshot.total_value > 0:
            total_return = (
                last_snapshot.total_value - first_snapshot.total_value
            ) / first_snapshot.total_value
            days = (last_snapshot.snapshot_date - first_snapshot.snapshot_date).days
            years = days / 365.25
            if years > 0:
                metrics.yearly_growth_rate = (
                    (1 + total_return) ** (Decimal("1") / Decimal(years)) - 1
                ) * 100
                months = days / 30.44
                if months > 0:
                    metrics.monthly_growth_rate = (
                        (1 + total_return) ** (Decimal("1") / Decimal(months)) - 1
                    ) * 100

        return metrics

    def get_historical_net_worth(self, period: str = "1y") -> list[dict]:
        """Get historical net worth data for charting.

        Args:
            period: Time period - "7d", "30d", "90d", "1y", "all"

        Returns:
            List of ``{date, net_worth, cost_basis}`` dicts (all CAD).
        """
        today = date.today()
        period_days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365, "all": 3650}
        days = period_days.get(period, 365)
        start_date = today - timedelta(days=days)

        snapshots = (
            self.db.query(PortfolioSnapshot)
            .filter(PortfolioSnapshot.snapshot_date >= start_date)
            .order_by(PortfolioSnapshot.snapshot_date.asc())
            .all()
        )

        return [
            {
                "date": snapshot.snapshot_date.isoformat(),
                "net_worth": float(snapshot.total_value),
                "cost_basis": float(snapshot.total_cost_basis),
            }
            for snapshot in snapshots
        ]


def get_insights_summary(db: Session) -> dict:
    """Get a complete insights summary for the dashboard (CAD)."""
    calculator = InsightsCalculator(db)
    net_worth = calculator.calculate_net_worth()
    allocation = calculator.calculate_allocation()
    growth = calculator.calculate_growth_metrics()

    def _f(v: Optional[Decimal]) -> Optional[float]:
        return float(v) if v is not None else None

    return {
        "net_worth": {
            "total_cad": float(net_worth.net_worth_cad),
            "total_assets_cad": float(net_worth.total_assets_cad),
            "total_liabilities_cad": float(net_worth.total_liabilities_cad),
            "liquid_assets_cad": float(net_worth.liquid_assets_cad),
            "investment_assets_cad": float(net_worth.investment_assets_cad),
            "retirement_assets_cad": float(net_worth.retirement_assets_cad),
            "real_estate_equity_cad": float(net_worth.real_estate_equity_cad),
            "change_1d": _f(net_worth.change_1d),
            "change_1d_percent": _f(net_worth.change_1d_percent),
            "change_1m": _f(net_worth.change_1m),
            "change_1m_percent": _f(net_worth.change_1m_percent),
            "change_ytd": _f(net_worth.change_ytd),
            "change_ytd_percent": _f(net_worth.change_ytd_percent),
        },
        "allocation": {
            "by_type": {k: float(v) for k, v in allocation.by_type.items()},
            "by_country": {k: float(v) for k, v in allocation.by_country.items()},
            "by_institution": {
                k: float(v) for k, v in allocation.by_institution.items()
            },
        },
        "growth": {
            "monthly_rate": float(growth.monthly_growth_rate),
            "yearly_rate": float(growth.yearly_growth_rate),
            "average_monthly": float(growth.average_monthly_growth),
            "best_month": growth.best_month.isoformat() if growth.best_month else None,
            "best_month_return": _f(growth.best_month_return),
            "worst_month": growth.worst_month.isoformat() if growth.worst_month else None,
            "worst_month_return": _f(growth.worst_month_return),
        },
    }
