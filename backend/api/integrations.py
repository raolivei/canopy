"""API endpoints for third-party integrations (Wise, Questrade, etc.)."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.app.config import get_settings
from backend.db.models.asset import Asset, AssetType, SyncSource
from backend.db.models.lot import Lot
from backend.db.models.transaction import Transaction as TransactionModel
from backend.db.session import DbSession
from backend.services.wise_integration import WISE_SYNC_CURRENCIES

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


# ==================== Wise Integration ====================


class WiseConnectRequest(BaseModel):
    """Request to connect Wise account."""

    api_token: str
    sandbox: bool = False


class WiseBalanceResponse(BaseModel):
    """Balance response from Wise."""

    currency: str
    amount: float
    reserved: float = 0


class WiseTransactionResponse(BaseModel):
    """Transaction response from Wise."""

    id: str
    date: datetime
    description: str
    amount: float
    currency: str
    transaction_type: str
    reference: Optional[str] = None
    merchant: Optional[str] = None


@router.get("/wise/status")
async def get_wise_status():
    """Return whether Wise is configured (token set via WISE_API_TOKEN env)."""
    settings = get_settings()
    return {"connected": bool(settings.wise_api_token)}


@router.post("/wise/test-connection")
async def test_wise_connection(request: WiseConnectRequest):
    """Test Wise API connection with provided token.

    Returns profile info if successful.
    """
    try:
        from backend.services.wise_integration import WiseIntegrationService

        with WiseIntegrationService(request.api_token, sandbox=request.sandbox) as wise:
            profiles = wise.get_profiles()
            personal = next((p for p in profiles if p.type == "personal"), None)

            if not personal:
                raise HTTPException(status_code=400, detail="No personal profile found")

            return {
                "status": "connected",
                "profile_id": personal.id,
                "name": f"{personal.first_name} {personal.last_name}".strip() or "Unknown",
            }

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired API token. Generate a new Personal Token in Wise Settings → API tokens.",
            )
        raise HTTPException(status_code=400, detail=f"Connection failed: {msg}")


@router.post("/wise/balances", response_model=list[WiseBalanceResponse])
async def get_wise_balances(request: WiseConnectRequest):
    """Get all currency balances from Wise."""
    try:
        from backend.services.wise_integration import WiseIntegrationService

        with WiseIntegrationService(request.api_token, sandbox=request.sandbox) as wise:
            balances = wise.get_balances()
            return [
                WiseBalanceResponse(
                    currency=b.currency,
                    amount=float(b.amount),
                    reserved=float(b.reserved),
                )
                for b in balances
            ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch balances: {str(e)}")


class WiseTransactionsRequest(BaseModel):
    """Request for Wise transactions."""

    api_token: str
    sandbox: bool = False
    currency: Optional[str] = None
    days: int = 90


@router.post("/wise/transactions", response_model=list[WiseTransactionResponse])
async def get_wise_transactions(request: WiseTransactionsRequest):
    """Get transactions from Wise.

    Optionally filter by currency. If no currency specified, returns all.
    """
    try:
        from backend.services.wise_integration import WiseIntegrationService

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=request.days)

        with WiseIntegrationService(request.api_token, sandbox=request.sandbox) as wise:
            if request.currency:
                transactions = wise.get_transactions(
                    currency=request.currency,
                    start_date=start_date,
                    end_date=end_date,
                )
            else:
                transactions = wise.get_all_transactions(
                    start_date=start_date,
                    end_date=end_date,
                )

            return [
                WiseTransactionResponse(
                    id=tx.id,
                    date=tx.date,
                    description=tx.description,
                    amount=float(tx.amount),
                    currency=tx.currency,
                    transaction_type=tx.transaction_type,
                    reference=tx.reference,
                    merchant=tx.merchant,
                )
                for tx in transactions
            ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch transactions: {str(e)}")


class WiseSyncRequest(BaseModel):
    """Request to sync Wise data into Canopy (assets + transactions)."""

    api_token: Optional[str] = None  # If omitted, uses WISE_API_TOKEN from env
    sandbox: bool = False
    days: int = 90


class WiseSyncResponse(BaseModel):
    """Response after syncing Wise data."""

    assets_created: int
    assets_updated: int
    transactions_imported: int
    currencies: list[str]
    skipped_currencies: list[str] = Field(default_factory=list)


@router.post("/wise/sync", response_model=WiseSyncResponse)
async def sync_wise_to_canopy(request: WiseSyncRequest, db: DbSession):
    """Fetch Wise balances and transactions, then upsert Canopy assets and import transactions.

    Only **CAD** and **USD** Wise balances are synced into Canopy (the product scope).
    Other pockets (e.g. JPY, EUR) are skipped until multi-currency FX is modeled end-to-end.
    """
    from backend.services.wise_integration import WiseIntegrationService

    token = request.api_token or get_settings().wise_api_token
    if not token:
        raise HTTPException(
            status_code=400,
            detail="No Wise token. Provide api_token in the request or set WISE_API_TOKEN.",
        )

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=request.days)
    assets_created = 0
    assets_updated = 0
    transactions_imported = 0
    currencies: list[str] = []
    skipped_currencies: list[str] = []
    now = datetime.now(timezone.utc)

    with WiseIntegrationService(token, sandbox=request.sandbox) as wise:
        all_balances = wise.get_balances()
        for b in all_balances:
            ccy = b.currency.upper()
            if ccy not in WISE_SYNC_CURRENCIES:
                skipped_currencies.append(b.currency)
                continue
            currencies.append(b.currency)
            symbol = f"WISE_{b.currency}"
            existing = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
            balance_value = Decimal(str(b.amount))
            if existing:
                existing.current_price = balance_value
                existing.price_updated_at = now
                assets_updated += 1
            else:
                asset = Asset(
                    symbol=symbol,
                    name=f"Wise {b.currency}",
                    asset_type=AssetType.BANK_ACCOUNT,
                    currency=b.currency,
                    institution="Wise",
                    sync_source="WISE",
                    current_price=balance_value,
                    price_updated_at=now,
                )
                db.add(asset)
                assets_created += 1

        transactions = wise.get_all_transactions(
            start_date=start_date,
            end_date=end_date,
            currencies=set(WISE_SYNC_CURRENCIES),
        )
        existing_ids = {
            row[0]
            for row in db.execute(
                select(TransactionModel.import_id).where(TransactionModel.import_source == "wise")
            ).all()
        }
        for tx in transactions:
            if (tx.currency or "").upper() not in WISE_SYNC_CURRENCIES:
                continue
            if tx.id in existing_ids:
                continue
            db.add(
                TransactionModel(
                    description=tx.description or "Wise transaction",
                    amount=Decimal(str(tx.amount)),
                    currency=tx.currency,
                    type="income" if tx.amount > 0 else "expense",
                    date=tx.date,
                    merchant=tx.merchant,
                    import_id=tx.id,
                    import_source="wise",
                )
            )
            transactions_imported += 1

    db.commit()
    return WiseSyncResponse(
        assets_created=assets_created,
        assets_updated=assets_updated,
        transactions_imported=transactions_imported,
        currencies=currencies,
        skipped_currencies=sorted(set(skipped_currencies)),
    )


# ==================== Questrade Integration ====================


class QuestradeConnectRequest(BaseModel):
    """Request to connect Questrade (manual authorization token from API Centre).

    If ``refresh_token`` is omitted or empty, the API uses ``QUESTRADE_REFRESH_TOKEN``
    from the environment (e.g. injected from Vault / External Secrets in cluster).
    A non-empty body value wins over the environment.
    """

    refresh_token: Optional[str] = None


class QuestradeAccountResponse(BaseModel):
    number: str
    type: str
    status: str
    is_primary: bool = False
    is_billing: bool = False
    client_account_type: str = ""


class QuestradePositionResponse(BaseModel):
    symbol_id: int
    symbol: str
    open_quantity: Decimal
    current_market_value: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    average_entry_price: Optional[Decimal] = None
    open_pnl: Optional[Decimal] = None
    closed_pnl: Optional[Decimal] = None


class QuestradeSyncResponse(BaseModel):
    """Summary after syncing Questrade into assets and lots."""

    accounts_synced: int
    assets_created: int
    assets_updated: int
    positions_synced: int
    created_lots: int = 0
    updated_lots: int = 0


@router.get("/questrade/status")
async def get_questrade_status():
    """Return whether ``QUESTRADE_REFRESH_TOKEN`` is set (e.g. Vault → External Secrets → pod env)."""
    settings = get_settings()
    return {"connected": bool((settings.questrade_refresh_token or "").strip())}


def _resolve_questrade_refresh_token(request: QuestradeConnectRequest) -> str:
    body = (request.refresh_token or "").strip()
    if body:
        return body
    env_token = (get_settings().questrade_refresh_token or "").strip()
    if env_token:
        return env_token
    raise HTTPException(
        status_code=400,
        detail=(
            "No Questrade refresh token. Paste a token in the UI, or set QUESTRADE_REFRESH_TOKEN "
            "(e.g. from Vault via External Secrets)."
        ),
    )


@router.post("/questrade/test-connection")
async def test_questrade_connection(request: QuestradeConnectRequest):
    """Test Questrade API connection with provided refresh token."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        token = _resolve_questrade_refresh_token(request)
        with QuestradeIntegrationService(token) as qt:
            accounts = qt.get_accounts()
            if not accounts:
                raise HTTPException(status_code=400, detail="No accounts found")
            primary = next((a for a in accounts if a.is_primary), accounts[0])
            return {
                "status": "connected",
                "accounts": [
                    QuestradeAccountResponse(
                        number=a.number,
                        type=a.type,
                        status=a.status,
                        is_primary=a.is_primary,
                        is_billing=a.is_billing,
                        client_account_type=a.client_account_type,
                    )
                    for a in accounts
                ],
                "accounts_count": len(accounts),
                "primary_account": primary.number,
                "primary_type": primary.type,
                "new_refresh_token": qt.refresh_token,
            }
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg or "invalid_grant" in msg:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token. In Questrade: API Centre → your personal app → New manual authorization → copy the token (see questrade.com/api/documentation/getting-started).",
            )
        raise HTTPException(status_code=400, detail=f"Connection failed: {msg}")


@router.post("/questrade/accounts", response_model=list[QuestradeAccountResponse])
async def get_questrade_accounts(request: QuestradeConnectRequest):
    """Fetch Questrade accounts."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        token = _resolve_questrade_refresh_token(request)
        with QuestradeIntegrationService(token) as qt:
            accounts = qt.get_accounts()
            return [
                QuestradeAccountResponse(
                    number=a.number,
                    type=a.type,
                    status=a.status,
                    is_primary=a.is_primary,
                    is_billing=a.is_billing,
                    client_account_type=a.client_account_type,
                )
                for a in accounts
            ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/questrade/positions", response_model=list[QuestradePositionResponse])
async def get_questrade_positions(
    request: QuestradeConnectRequest,
    account_number: str = Query(..., description="Questrade account number"),
):
    """Fetch positions for a Questrade account (account number as query param)."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        token = _resolve_questrade_refresh_token(request)
        with QuestradeIntegrationService(token) as qt:
            positions = qt.get_positions(account_number)
            return [
                QuestradePositionResponse(
                    symbol_id=p.symbol_id,
                    symbol=p.symbol,
                    open_quantity=p.open_quantity,
                    current_market_value=p.current_market_value,
                    current_price=p.current_price,
                    average_entry_price=p.average_entry_price,
                    open_pnl=p.open_pnl,
                    closed_pnl=p.closed_pnl,
                )
                for p in positions
            ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/questrade/sync", response_model=QuestradeSyncResponse)
async def sync_questrade(request: QuestradeConnectRequest, db: DbSession):
    """Sync Questrade accounts and positions into Canopy assets and lots (per-account lots)."""
    from backend.services.questrade_integration import QuestradeIntegrationService

    created_assets = 0
    created_lots = 0
    updated_lots = 0

    token = _resolve_questrade_refresh_token(request)
    with QuestradeIntegrationService(token) as qt:
        accounts = qt.get_accounts()

        for acc in accounts:
            positions = qt.get_positions(acc.number)
            for pos in positions:
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
                    select(Lot)
                    .where(Lot.asset_id == asset.id)
                    .where(Lot.account == account_label)
                ).scalar_one_or_none()

                if lot:
                    lot.quantity = pos.open_quantity
                    lot.price_per_unit = price
                    updated_lots += 1
                else:
                    db.add(
                        Lot(
                            asset_id=asset.id,
                            quantity=pos.open_quantity,
                            price_per_unit=price,
                            fees=Decimal("0"),
                            purchase_date=date.today(),
                            account=account_label,
                            notes=f"Synced from Questrade {acc.type}",
                        )
                    )
                    created_lots += 1

        db.commit()

    return QuestradeSyncResponse(
        accounts_synced=len(accounts),
        assets_created=created_assets,
        assets_updated=updated_lots,
        positions_synced=created_lots + updated_lots,
        created_lots=created_lots,
        updated_lots=updated_lots,
    )


# ==================== Integration Status ====================


@router.get("/status")
async def get_integration_status():
    """Get status of all available integrations."""
    return {
        "integrations": [
            {
                "id": "wise",
                "name": "Wise (TransferWise)",
                "type": "api",
                "status": "available",
                "description": "Multi-currency account with global transfers",
                "requires_token": True,
                "supported_features": ["balances", "transactions"],
            },
            {
                "id": "questrade",
                "name": "Questrade",
                "type": "api",
                "status": "available",
                "description": "Canadian discount brokerage (TFSA, RRSP, trading)",
                "requires_token": True,
                "supported_features": ["accounts", "positions", "balances"],
            },
            {
                "id": "csv_import",
                "name": "CSV Import",
                "type": "file",
                "status": "available",
                "description": "Import transactions from CSV exports",
                "supported_formats": [
                    "Nubank",
                    "Clear Investimentos",
                    "XP Investimentos",
                    "RBC Canada",
                    "Wealthsimple",
                    "Schwab",
                    "Wise",
                    "Chase",
                    "Bank of America",
                    "Capital One",
                    "Amex",
                ],
            },
        ],
        "coming_soon": [
            {
                "id": "plaid",
                "name": "Plaid",
                "description": "Automatic bank connections for US/Canada",
            },
        ],
    }


# ==================== CSV Format Info ====================


@router.get("/csv-formats")
async def get_csv_formats():
    """Get information about supported CSV formats."""
    return {
        "formats": [
            {
                "id": "rbc",
                "name": "RBC Royal Bank",
                "country": "Canada",
                "type": "bank",
                "export_instructions": "Online Banking > Accounts > Download Transactions",
                "sample_headers": ["Transaction Date", "Description 1", "CAD$", "Account Number"],
            },
            {
                "id": "wealthsimple",
                "name": "Wealthsimple Cash",
                "country": "Canada",
                "type": "bank",
                "export_instructions": "App > Account > Statements > Download CSV",
                "sample_headers": ["Date", "Description", "Amount", "Currency", "Account"],
            },
            {
                "id": "wealthsimple_trade",
                "name": "Wealthsimple Trade",
                "country": "Canada",
                "type": "brokerage",
                "export_instructions": "App > Activity > Export (request via support)",
                "sample_headers": [
                    "Date",
                    "Transaction Type",
                    "Symbol",
                    "Quantity",
                    "Price",
                    "Market Value",
                    "Currency",
                ],
            },
            {
                "id": "schwab",
                "name": "Charles Schwab",
                "country": "USA",
                "type": "brokerage",
                "export_instructions": "Accounts > History > Export",
                "sample_headers": [
                    "Date",
                    "Action",
                    "Symbol",
                    "Description",
                    "Quantity",
                    "Price",
                    "Fees & Comm",
                    "Amount",
                ],
            },
            {
                "id": "wise",
                "name": "Wise",
                "country": "Global",
                "type": "bank",
                "export_instructions": "Account > Statement > Download CSV",
                "sample_headers": [
                    "Date",
                    "Description",
                    "Amount",
                    "Currency",
                    "Running Balance",
                    "TransferWise ID",
                ],
                "notes": "Also supports direct API integration",
            },
        ],
    }
