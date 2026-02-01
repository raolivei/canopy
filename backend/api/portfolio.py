"""Portfolio API endpoints for asset, lot, and dividend management."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from backend.db.session import DbSession
from backend.db.models.asset import Asset, AssetType
from backend.db.models.lot import Lot
from backend.db.models.dividend import Dividend
from backend.models.portfolio_schemas import (
    AssetCreate,
    AssetResponse,
    AssetWithHoldings,
    LotCreate,
    LotSell,
    LotResponse,
    DividendCreate,
    DividendResponse,
    PortfolioSummary,
    PortfolioAllocation,
)
from backend.services.portfolio_calculator import PortfolioCalculator


router = APIRouter(prefix="/v1/portfolio", tags=["portfolio"])


# ============== Asset Endpoints ==============

@router.post("/assets", response_model=AssetResponse)
async def create_asset(asset_data: AssetCreate, db: DbSession):
    """Add a new asset to track."""
    # Check if symbol already exists
    existing = db.execute(
        select(Asset).where(Asset.symbol == asset_data.symbol.upper())
    ).scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"Asset {asset_data.symbol} already exists")
    
    asset = Asset(
        symbol=asset_data.symbol.upper(),
        name=asset_data.name,
        asset_type=asset_data.asset_type,
        currency=asset_data.currency.upper(),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/assets", response_model=list[AssetWithHoldings])
async def list_assets(
    db: DbSession,
    asset_type: Optional[AssetType] = Query(None, description="Filter by asset type"),
):
    """List all tracked assets with holdings data."""
    query = select(Asset)
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)
    
    assets = db.execute(query.order_by(Asset.symbol)).scalars().all()
    calculator = PortfolioCalculator(db)
    
    result = []
    for asset in assets:
        summary = calculator.get_holding_summary(asset)
        result.append(AssetWithHoldings(
            id=asset.id,
            symbol=asset.symbol,
            name=asset.name,
            asset_type=asset.asset_type,
            currency=asset.currency,
            created_at=asset.created_at,
            current_price=asset.current_price,
            price_updated_at=asset.price_updated_at,
            total_shares=summary.total_shares,
            average_cost=summary.average_cost,
            total_cost_basis=summary.cost_basis,
            market_value=summary.market_value,
            unrealized_gain_loss=summary.unrealized_gain_loss,
            return_pct=summary.return_pct,
        ))
    
    return result


@router.get("/assets/{asset_id}", response_model=AssetWithHoldings)
async def get_asset(asset_id: int, db: DbSession):
    """Get a specific asset with holdings data."""
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    calculator = PortfolioCalculator(db)
    summary = calculator.get_holding_summary(asset)
    
    return AssetWithHoldings(
        id=asset.id,
        symbol=asset.symbol,
        name=asset.name,
        asset_type=asset.asset_type,
        currency=asset.currency,
        created_at=asset.created_at,
        current_price=asset.current_price,
        price_updated_at=asset.price_updated_at,
        total_shares=summary.total_shares,
        average_cost=summary.average_cost,
        total_cost_basis=summary.cost_basis,
        market_value=summary.market_value,
        unrealized_gain_loss=summary.unrealized_gain_loss,
        return_pct=summary.return_pct,
    )


@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: int, db: DbSession):
    """Delete an asset and all its lots and dividends."""
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    db.delete(asset)
    db.commit()
    return {"message": f"Asset {asset.symbol} deleted"}


# ============== Lot Endpoints ==============

@router.post("/lots", response_model=LotResponse)
async def create_lot(lot_data: LotCreate, db: DbSession):
    """Add a new purchase lot (buy transaction)."""
    # Verify asset exists
    asset = db.execute(
        select(Asset).where(Asset.id == lot_data.asset_id)
    ).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    lot = Lot(
        asset_id=lot_data.asset_id,
        quantity=lot_data.quantity,
        price_per_unit=lot_data.price_per_unit,
        fees=lot_data.fees,
        purchase_date=lot_data.purchase_date,
        account=lot_data.account,
        notes=lot_data.notes,
    )
    db.add(lot)
    db.commit()
    db.refresh(lot)
    
    return LotResponse(
        id=lot.id,
        asset_id=lot.asset_id,
        quantity=lot.quantity,
        price_per_unit=lot.price_per_unit,
        fees=lot.fees,
        purchase_date=lot.purchase_date,
        account=lot.account,
        notes=lot.notes,
        is_sold=lot.is_sold,
        sold_date=lot.sold_date,
        sold_price_per_unit=lot.sold_price_per_unit,
        sold_fees=lot.sold_fees,
        created_at=lot.created_at,
        cost_basis=lot.cost_basis,
        realized_gain_loss=lot.realized_gain_loss,
    )


@router.get("/lots", response_model=list[LotResponse])
async def list_lots(
    db: DbSession,
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    include_sold: bool = Query(False, description="Include sold lots"),
):
    """List all purchase lots."""
    query = select(Lot)
    if asset_id:
        query = query.where(Lot.asset_id == asset_id)
    if not include_sold:
        query = query.where(Lot.is_sold == False)
    
    lots = db.execute(query.order_by(Lot.purchase_date)).scalars().all()
    
    return [
        LotResponse(
            id=lot.id,
            asset_id=lot.asset_id,
            quantity=lot.quantity,
            price_per_unit=lot.price_per_unit,
            fees=lot.fees,
            purchase_date=lot.purchase_date,
            account=lot.account,
            notes=lot.notes,
            is_sold=lot.is_sold,
            sold_date=lot.sold_date,
            sold_price_per_unit=lot.sold_price_per_unit,
            sold_fees=lot.sold_fees,
            created_at=lot.created_at,
            cost_basis=lot.cost_basis,
            realized_gain_loss=lot.realized_gain_loss,
        )
        for lot in lots
    ]


@router.put("/lots/{lot_id}/sell", response_model=LotResponse)
async def sell_lot(lot_id: int, sell_data: LotSell, db: DbSession):
    """Mark a lot as sold."""
    lot = db.execute(
        select(Lot).where(Lot.id == lot_id)
    ).scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    if lot.is_sold:
        raise HTTPException(status_code=400, detail="Lot already sold")
    
    lot.is_sold = True
    lot.sold_date = sell_data.sold_date
    lot.sold_price_per_unit = sell_data.sold_price_per_unit
    lot.sold_fees = sell_data.sold_fees
    
    db.commit()
    db.refresh(lot)
    
    return LotResponse(
        id=lot.id,
        asset_id=lot.asset_id,
        quantity=lot.quantity,
        price_per_unit=lot.price_per_unit,
        fees=lot.fees,
        purchase_date=lot.purchase_date,
        account=lot.account,
        notes=lot.notes,
        is_sold=lot.is_sold,
        sold_date=lot.sold_date,
        sold_price_per_unit=lot.sold_price_per_unit,
        sold_fees=lot.sold_fees,
        created_at=lot.created_at,
        cost_basis=lot.cost_basis,
        realized_gain_loss=lot.realized_gain_loss,
    )


@router.delete("/lots/{lot_id}")
async def delete_lot(lot_id: int, db: DbSession):
    """Delete a lot."""
    lot = db.execute(
        select(Lot).where(Lot.id == lot_id)
    ).scalar_one_or_none()
    
    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")
    
    db.delete(lot)
    db.commit()
    return {"message": "Lot deleted"}


# ============== Dividend Endpoints ==============

@router.post("/dividends", response_model=DividendResponse)
async def create_dividend(dividend_data: DividendCreate, db: DbSession):
    """Record a dividend payment."""
    # Verify asset exists
    asset = db.execute(
        select(Asset).where(Asset.id == dividend_data.asset_id)
    ).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    dividend = Dividend(
        asset_id=dividend_data.asset_id,
        amount=dividend_data.amount,
        payment_date=dividend_data.payment_date,
        dividend_type=dividend_data.dividend_type,
        shares_received=dividend_data.shares_received,
        notes=dividend_data.notes,
    )
    db.add(dividend)
    db.commit()
    db.refresh(dividend)
    
    return DividendResponse(
        id=dividend.id,
        asset_id=dividend.asset_id,
        amount=dividend.amount,
        payment_date=dividend.payment_date,
        dividend_type=dividend.dividend_type,
        shares_received=dividend.shares_received,
        notes=dividend.notes,
        created_at=dividend.created_at,
        asset_symbol=asset.symbol,
    )


@router.get("/dividends", response_model=list[DividendResponse])
async def list_dividends(
    db: DbSession,
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
):
    """List dividend payments."""
    query = select(Dividend, Asset.symbol).join(Asset)
    
    if asset_id:
        query = query.where(Dividend.asset_id == asset_id)
    if start_date:
        query = query.where(Dividend.payment_date >= start_date)
    if end_date:
        query = query.where(Dividend.payment_date <= end_date)
    
    results = db.execute(query.order_by(Dividend.payment_date.desc())).all()
    
    return [
        DividendResponse(
            id=dividend.id,
            asset_id=dividend.asset_id,
            amount=dividend.amount,
            payment_date=dividend.payment_date,
            dividend_type=dividend.dividend_type,
            shares_received=dividend.shares_received,
            notes=dividend.notes,
            created_at=dividend.created_at,
            asset_symbol=symbol,
        )
        for dividend, symbol in results
    ]


@router.delete("/dividends/{dividend_id}")
async def delete_dividend(dividend_id: int, db: DbSession):
    """Delete a dividend record."""
    dividend = db.execute(
        select(Dividend).where(Dividend.id == dividend_id)
    ).scalar_one_or_none()
    
    if not dividend:
        raise HTTPException(status_code=404, detail="Dividend not found")
    
    db.delete(dividend)
    db.commit()
    return {"message": "Dividend deleted"}


# ============== Portfolio Summary Endpoints ==============

@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: DbSession):
    """Get complete portfolio summary with all holdings and metrics."""
    calculator = PortfolioCalculator(db)
    return calculator.get_portfolio_summary()


@router.get("/allocation", response_model=PortfolioAllocation)
async def get_portfolio_allocation(db: DbSession):
    """Get portfolio allocation breakdown by asset type."""
    calculator = PortfolioCalculator(db)
    return calculator.get_allocation()


# ============== Price Endpoints ==============

@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """Look up a stock/ETF/crypto quote by symbol.
    
    Useful for validating symbols before adding them.
    """
    from backend.services.price_fetcher import fetch_quote
    
    quote = fetch_quote(symbol.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Could not find quote for {symbol}")
    
    return quote


@router.post("/prices/refresh")
async def refresh_all_prices(db: DbSession):
    """Manually trigger a price refresh for all assets."""
    from backend.services.price_fetcher import PriceFetcher
    
    fetcher = PriceFetcher(db)
    results = fetcher.update_all_prices()
    
    success_count = sum(1 for v in results.values() if v)
    return {
        "message": f"Refreshed {success_count}/{len(results)} prices",
        "results": results,
    }


@router.post("/prices/refresh/{asset_id}")
async def refresh_asset_price(asset_id: int, db: DbSession):
    """Manually refresh price for a single asset."""
    from backend.services.price_fetcher import PriceFetcher
    
    asset = db.execute(
        select(Asset).where(Asset.id == asset_id)
    ).scalar_one_or_none()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    fetcher = PriceFetcher(db)
    success = fetcher.update_asset_price(asset)
    
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {asset.symbol}")
    
    return {
        "message": f"Updated price for {asset.symbol}",
        "price": str(asset.current_price),
    }


# ============== Performance/History Endpoints ==============

@router.get("/performance")
async def get_portfolio_performance(
    db: DbSession,
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 1y, all"),
):
    """Get historical portfolio performance data for charting."""
    from datetime import datetime, timedelta
    from backend.db.models.portfolio_snapshot import PortfolioSnapshot
    
    # Calculate date cutoff based on period
    today = date.today()
    if period == "7d":
        cutoff = today - timedelta(days=7)
    elif period == "30d":
        cutoff = today - timedelta(days=30)
    elif period == "90d":
        cutoff = today - timedelta(days=90)
    elif period == "1y":
        cutoff = today - timedelta(days=365)
    else:  # "all"
        cutoff = None
    
    # Query snapshots
    query = select(PortfolioSnapshot).order_by(PortfolioSnapshot.snapshot_date)
    if cutoff:
        query = query.where(PortfolioSnapshot.snapshot_date >= cutoff)
    
    snapshots = db.execute(query).scalars().all()
    
    data_points = []
    for snapshot in snapshots:
        gain_loss = snapshot.total_value - snapshot.total_cost_basis
        return_pct = None
        if snapshot.total_cost_basis > 0:
            return_pct = float((gain_loss / snapshot.total_cost_basis) * 100)
        
        data_points.append({
            "date": str(snapshot.snapshot_date),
            "total_value": float(snapshot.total_value),
            "total_cost_basis": float(snapshot.total_cost_basis),
            "gain_loss": float(gain_loss),
            "return_pct": return_pct,
        })
    
    # Calculate period metrics
    start_value = data_points[0]["total_value"] if data_points else None
    end_value = data_points[-1]["total_value"] if data_points else None
    period_return = None
    period_return_pct = None
    
    if start_value and end_value and start_value > 0:
        period_return = end_value - start_value
        period_return_pct = (period_return / start_value) * 100
    
    return {
        "period": period,
        "data_points": data_points,
        "start_value": start_value,
        "end_value": end_value,
        "period_return": period_return,
        "period_return_pct": period_return_pct,
    }


@router.post("/snapshots/create")
async def create_snapshot_now(db: DbSession):
    """Manually trigger snapshot creation for today."""
    from backend.ingest.tasks import create_daily_snapshot
    
    # Call the task synchronously (not via Celery)
    result = create_daily_snapshot()
    return result


@router.get("/snapshots")
async def list_snapshots(
    db: DbSession,
    limit: int = Query(30, description="Number of snapshots to return"),
):
    """List recent portfolio snapshots."""
    from backend.db.models.portfolio_snapshot import PortfolioSnapshot
    
    snapshots = db.execute(
        select(PortfolioSnapshot)
        .order_by(PortfolioSnapshot.snapshot_date.desc())
        .limit(limit)
    ).scalars().all()
    
    return [
        {
            "id": s.id,
            "date": str(s.snapshot_date),
            "total_value": float(s.total_value),
            "total_cost_basis": float(s.total_cost_basis),
            "gain_loss": float(s.total_value - s.total_cost_basis),
        }
        for s in snapshots
    ]
