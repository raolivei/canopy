"""Background data ingestion tasks executed by Celery."""

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select

from backend.app.config import get_settings
from backend.db.session import SessionLocal
from backend.db.models.asset import Asset, AssetType, SyncSource
from backend.db.models.lot import Lot
from backend.db.models.portfolio_snapshot import PortfolioSnapshot, SnapshotHolding

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "canopy_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    # Update prices every 15 minutes during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
    "update-prices-market-hours": {
        "task": "ingest.update_all_prices",
        "schedule": crontab(minute="*/15", hour="9-16", day_of_week="1-5"),
    },
    # Create daily snapshot at 5 PM ET (after market close)
    "create-daily-snapshot": {
        "task": "ingest.create_daily_snapshot",
        "schedule": crontab(minute=0, hour=17, day_of_week="1-5"),
    },
    # Sync Questrade positions (if QUESTRADE_REFRESH_TOKEN set) - daily at 6 PM ET
    "sync-questrade": {
        "task": "ingest.sync_questrade",
        "schedule": crontab(minute=0, hour=18, day_of_week="1-5"),
    },
}

celery_app.conf.timezone = "America/New_York"


@celery_app.task(name="ingest.import_csv")
def import_csv(file_path: str) -> str:
    """Placeholder CSV import task."""
    return f"CSV import queued for {file_path}"


@celery_app.task(name="ingest.sync_questrade")
def sync_questrade(refresh_token: Optional[str] = None) -> dict:
    """Sync Questrade accounts and positions into Canopy. Uses refresh_token or settings."""
    token = refresh_token or get_settings().questrade_refresh_token
    if not token:
        logger.warning("Questrade sync skipped: no refresh token")
        return {"status": "skipped", "reason": "no_refresh_token"}
    from backend.services.questrade_integration import QuestradeIntegrationService
    db = SessionLocal()
    try:
        with QuestradeIntegrationService(token) as qt:
            accounts = qt.get_accounts()
            created_assets = created_lots = updated_lots = 0
            for acc in accounts:
                for pos in qt.get_positions(acc.number):
                    symbol = (pos.symbol or "").strip().upper()
                    if not symbol:
                        continue
                    price = pos.average_entry_price or pos.current_price or Decimal("0")
                    if price <= 0:
                        price = Decimal("0.01")
                    asset = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
                    if not asset:
                        asset = Asset(
                            symbol=symbol,
                            name=symbol,
                            asset_type=AssetType.STOCK,
                            currency="CAD",
                            institution="Questrade",
                            country="CA",
                            sync_source=SyncSource.QUESTRADE.value,
                            external_account_id=acc.number,
                        )
                        db.add(asset)
                        db.flush()
                        created_assets += 1
                    account_label = f"Questrade-{acc.number}"
                    lot = db.execute(
                        select(Lot).where(Lot.asset_id == asset.id).where(Lot.account == account_label)
                    ).scalar_one_or_none()
                    if lot:
                        lot.quantity = pos.open_quantity
                        lot.price_per_unit = price
                        updated_lots += 1
                    else:
                        db.add(Lot(
                            asset_id=asset.id,
                            quantity=pos.open_quantity,
                            price_per_unit=price,
                            fees=Decimal("0"),
                            purchase_date=date.today(),
                            account=account_label,
                            notes=f"Synced from Questrade {acc.type}",
                        ))
                        created_lots += 1
            db.commit()
            logger.info(f"Questrade sync: {len(accounts)} accounts, +{created_assets} assets, +{created_lots} lots, ~{updated_lots} updated")
            return {"status": "synced", "accounts": len(accounts), "created_assets": created_assets, "created_lots": created_lots, "updated_lots": updated_lots}
    except Exception as e:
        logger.exception("Questrade sync failed")
        return {"status": "error", "detail": str(e)}
    finally:
        db.close()


@celery_app.task(name="ingest.update_all_prices")
def update_all_prices() -> dict:
    """Update prices for all tracked assets.
    
    Returns dict with results per symbol.
    """
    # Import here to avoid circular imports
    from backend.services.price_fetcher import PriceFetcher
    
    db = SessionLocal()
    try:
        fetcher = PriceFetcher(db)
        results = fetcher.update_all_prices()
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Price update complete: {success_count}/{len(results)} updated")
        
        return results
    finally:
        db.close()


@celery_app.task(name="ingest.update_asset_price")
def update_asset_price(asset_id: int) -> bool:
    """Update price for a single asset."""
    from backend.services.price_fetcher import PriceFetcher
    
    db = SessionLocal()
    try:
        asset = db.execute(
            select(Asset).where(Asset.id == asset_id)
        ).scalar_one_or_none()
        
        if not asset:
            logger.error(f"Asset {asset_id} not found")
            return False
        
        fetcher = PriceFetcher(db)
        return fetcher.update_asset_price(asset)
    finally:
        db.close()


@celery_app.task(name="ingest.create_daily_snapshot")
def create_daily_snapshot() -> dict:
    """Create a daily portfolio snapshot.
    
    Captures total portfolio value, cost basis, and per-asset breakdown.
    """
    db = SessionLocal()
    try:
        today = date.today()
        
        # Check if snapshot already exists for today
        existing = db.execute(
            select(PortfolioSnapshot).where(PortfolioSnapshot.snapshot_date == today)
        ).scalar_one_or_none()
        
        if existing:
            logger.info(f"Snapshot already exists for {today}")
            return {"status": "exists", "date": str(today)}
        
        # Get all assets with unsold lots
        assets = db.execute(select(Asset)).scalars().all()
        
        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        holdings_data = []
        
        for asset in assets:
            # Calculate totals from unsold lots
            lots = db.execute(
                select(Lot)
                .where(Lot.asset_id == asset.id)
                .where(Lot.is_sold == False)
            ).scalars().all()
            
            if not lots:
                continue
            
            quantity = sum(lot.quantity for lot in lots)
            cost_basis = sum(lot.cost_basis for lot in lots)
            
            # Market value requires current price
            if asset.current_price is not None:
                market_value = quantity * asset.current_price
            else:
                market_value = cost_basis  # Fallback to cost basis
            
            holdings_data.append({
                "asset": asset,
                "quantity": quantity,
                "cost_basis": cost_basis,
                "market_value": market_value,
                "price": asset.current_price or (cost_basis / quantity if quantity > 0 else Decimal("0")),
            })
            
            total_value += market_value
            total_cost_basis += cost_basis
        
        # Create snapshot
        snapshot = PortfolioSnapshot(
            snapshot_date=today,
            total_value=total_value,
            total_cost_basis=total_cost_basis,
        )
        db.add(snapshot)
        db.flush()  # Get snapshot ID
        
        # Create holdings
        for data in holdings_data:
            holding = SnapshotHolding(
                snapshot_id=snapshot.id,
                asset_id=data["asset"].id,
                quantity=data["quantity"],
                cost_basis=data["cost_basis"],
                market_value=data["market_value"],
                price_at_snapshot=data["price"],
            )
            db.add(holding)
        
        db.commit()
        
        logger.info(f"Created snapshot for {today}: value=${total_value}, holdings={len(holdings_data)}")
        
        return {
            "status": "created",
            "date": str(today),
            "total_value": str(total_value),
            "total_cost_basis": str(total_cost_basis),
            "holdings_count": len(holdings_data),
        }
        
    finally:
        db.close()
