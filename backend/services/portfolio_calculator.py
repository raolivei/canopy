"""Portfolio calculation service for metrics, cost basis, and performance."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db.models.asset import Asset
from backend.db.models.lot import Lot
from backend.db.models.dividend import Dividend
from backend.models.portfolio_schemas import (
    HoldingSummary,
    PortfolioSummary,
    AllocationItem,
    PortfolioAllocation,
)


class PortfolioCalculator:
    """Calculates portfolio metrics and summaries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_holding_summary(self, asset: Asset) -> HoldingSummary:
        """Calculate summary metrics for a single holding."""
        lots = self.db.execute(
            select(Lot)
            .where(Lot.asset_id == asset.id)
            .where(Lot.is_sold == False)
            .order_by(Lot.purchase_date)
        ).scalars().all()
        
        if not lots:
            return HoldingSummary(
                asset_id=asset.id,
                symbol=asset.symbol,
                name=asset.name,
                asset_type=asset.asset_type,
                total_shares=Decimal("0"),
                average_cost=Decimal("0"),
                current_price=asset.current_price,
                cost_basis=Decimal("0"),
                market_value=Decimal("0") if asset.current_price else None,
                unrealized_gain_loss=Decimal("0") if asset.current_price else None,
                return_pct=None,
                allocation_pct=None,
            )
        
        total_shares = sum(lot.quantity for lot in lots)
        total_cost_basis = sum(lot.cost_basis for lot in lots)
        average_cost = total_cost_basis / total_shares if total_shares > 0 else Decimal("0")
        
        market_value = None
        unrealized_gain_loss = None
        return_pct = None
        
        if asset.current_price is not None:
            market_value = total_shares * asset.current_price
            unrealized_gain_loss = market_value - total_cost_basis
            if total_cost_basis > 0:
                return_pct = (unrealized_gain_loss / total_cost_basis) * 100
        
        return HoldingSummary(
            asset_id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            total_shares=total_shares,
            average_cost=average_cost,
            current_price=asset.current_price,
            cost_basis=total_cost_basis,
            market_value=market_value,
            unrealized_gain_loss=unrealized_gain_loss,
            return_pct=return_pct,
            allocation_pct=None,
        )
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Calculate complete portfolio summary with all holdings."""
        assets = self.db.execute(select(Asset)).scalars().all()
        
        holdings = []
        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        has_prices = False
        
        for asset in assets:
            summary = self.get_holding_summary(asset)
            if summary.total_shares > 0:
                holdings.append(summary)
                total_cost_basis += summary.cost_basis
                if summary.market_value is not None:
                    total_value += summary.market_value
                    has_prices = True
        
        if has_prices and total_value > 0:
            for holding in holdings:
                if holding.market_value is not None:
                    holding.allocation_pct = (holding.market_value / total_value) * 100
        
        total_dividends = self.db.execute(
            select(func.coalesce(func.sum(Dividend.amount), 0))
        ).scalar() or Decimal("0")
        
        total_gain_loss = None
        total_return_pct = None
        
        if has_prices:
            total_gain_loss = total_value - total_cost_basis
            if total_cost_basis > 0:
                total_return_pct = (total_gain_loss / total_cost_basis) * 100
        
        return PortfolioSummary(
            total_value=total_value if has_prices else None,
            total_cost_basis=total_cost_basis,
            total_gain_loss=total_gain_loss,
            total_return_pct=total_return_pct,
            total_dividends=total_dividends,
            holdings_count=len(holdings),
            holdings=holdings,
        )
    
    def get_allocation(self) -> PortfolioAllocation:
        """Calculate portfolio allocation by asset type."""
        summary = self.get_portfolio_summary()
        
        type_totals = {}
        total_value = Decimal("0")
        
        for holding in summary.holdings:
            asset_type = holding.asset_type.value
            if holding.market_value is not None:
                if asset_type not in type_totals:
                    type_totals[asset_type] = {"value": Decimal("0"), "count": 0}
                type_totals[asset_type]["value"] += holding.market_value
                type_totals[asset_type]["count"] += 1
                total_value += holding.market_value
        
        allocations = []
        for asset_type, data in type_totals.items():
            percentage = (data["value"] / total_value * 100) if total_value > 0 else Decimal("0")
            allocations.append(AllocationItem(
                asset_type=asset_type,
                value=data["value"],
                percentage=percentage,
                count=data["count"],
            ))
        
        allocations.sort(key=lambda x: x.value, reverse=True)
        
        return PortfolioAllocation(
            by_asset_type=allocations,
            total_value=total_value,
        )
    
    def get_asset_with_totals(self, asset: Asset) -> dict:
        """Get asset with calculated total shares and cost basis."""
        summary = self.get_holding_summary(asset)
        return {
            "asset": asset,
            "total_shares": summary.total_shares,
            "average_cost": summary.average_cost,
            "total_cost_basis": summary.cost_basis,
            "market_value": summary.market_value,
            "unrealized_gain_loss": summary.unrealized_gain_loss,
            "return_pct": summary.return_pct,
        }
