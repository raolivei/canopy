"""API endpoints for third-party integrations (Wise, etc.)."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from backend.app.config import get_settings
from backend.db.models.asset import Asset, AssetType
from backend.db.models.transaction import Transaction as TransactionModel
from backend.db.session import DbSession

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


@router.post("/wise/sync", response_model=WiseSyncResponse)
async def sync_wise_to_canopy(request: WiseSyncRequest, db: DbSession):
    """Fetch Wise balances and transactions, then upsert Canopy assets and import transactions."""
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

    with WiseIntegrationService(token, sandbox=request.sandbox) as wise:
        balances = wise.get_balances()
        for b in balances:
            currencies.append(b.currency)
            symbol = f"WISE_{b.currency}"
            existing = db.execute(select(Asset).where(Asset.symbol == symbol)).scalar_one_or_none()
            if existing:
                # Could update balance-related fields here if we stored current_balance on Asset
                assets_updated += 1
            else:
                asset = Asset(
                    symbol=symbol,
                    name=f"Wise {b.currency}",
                    asset_type=AssetType.BANK_ACCOUNT,
                    currency=b.currency,
                    institution="Wise",
                    sync_source="WISE",
                )
                db.add(asset)
                assets_created += 1

        transactions = wise.get_all_transactions(start_date=start_date, end_date=end_date)
        existing_ids = {
            row[0]
            for row in db.execute(
                select(TransactionModel.import_id).where(TransactionModel.import_source == "wise")
            ).all()
        }
        for tx in transactions:
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
    )


# ==================== Questrade Integration ====================


class QuestradeConnectRequest(BaseModel):
    """Request to connect Questrade account."""

    refresh_token: str


class QuestradeAccountResponse(BaseModel):
    number: str
    type: str
    status: str


class QuestradePositionResponse(BaseModel):
    symbol: str
    quantity: float
    market_value: Optional[float] = None
    current_price: Optional[float] = None
    avg_entry_price: Optional[float] = None
    open_pnl: Optional[float] = None


class QuestradeBalanceResponse(BaseModel):
    currency: str
    cash: float
    market_value: float
    total_equity: float


class QuestradeSyncResponse(BaseModel):
    accounts_synced: int
    assets_created: int
    assets_updated: int
    positions_synced: int


QUESTRADE_TOKEN_KEY = "questrade_refresh_token"


@router.post("/questrade/test-connection")
async def test_questrade_connection(request: QuestradeConnectRequest):
    """Test Questrade API connection with provided refresh token."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            accounts = qt.get_accounts()
            if not accounts:
                raise HTTPException(status_code=400, detail="No accounts found")
            return {
                "status": "connected",
                "accounts": [QuestradeAccountResponse(number=a.number, type=a.type, status=a.status) for a in accounts],
                "new_refresh_token": qt.refresh_token,
            }
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg or "invalid_grant" in msg:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token. Generate a new one at my.questrade.com/APIAccess.",
            )
        raise HTTPException(status_code=400, detail=f"Connection failed: {msg}")


@router.post("/questrade/accounts", response_model=list[QuestradeAccountResponse])
async def get_questrade_accounts(request: QuestradeConnectRequest):
    """Fetch Questrade accounts."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            accounts = qt.get_accounts()
            return [QuestradeAccountResponse(number=a.number, type=a.type, status=a.status) for a in accounts]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/questrade/positions", response_model=list[QuestradePositionResponse])
async def get_questrade_positions(
    request: QuestradeConnectRequest,
    account_number: str = Query(..., description="Questrade account number"),
):
    """Fetch positions for a Questrade account."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            positions = qt.get_positions(account_number)
            return [
                QuestradePositionResponse(
                    symbol=p.symbol,
                    quantity=float(p.open_quantity),
                    market_value=float(p.current_market_value) if p.current_market_value else None,
                    current_price=float(p.current_price) if p.current_price else None,
                    avg_entry_price=float(p.average_entry_price) if p.average_entry_price else None,
                    open_pnl=float(p.open_pnl) if p.open_pnl else None,
                )
                for p in positions
            ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/questrade/sync", response_model=QuestradeSyncResponse)
async def sync_questrade(request: QuestradeConnectRequest, db: DbSession):
    """Sync Questrade accounts and positions into Canopy portfolio."""
    from backend.services.questrade_integration import QuestradeIntegrationService

    assets_created = 0
    assets_updated = 0
    positions_synced = 0

    with QuestradeIntegrationService(request.refresh_token) as qt:
        accounts = qt.get_accounts()

        for account in accounts:
            positions = qt.get_positions(account.number)
            for pos in positions:
                symbol = pos.symbol
                existing = db.execute(
                    select(Asset).where(Asset.symbol == symbol, Asset.sync_source == "QUESTRADE")
                ).scalar_one_or_none()

                if existing:
                    assets_updated += 1
                else:
                    asset = Asset(
                        symbol=symbol,
                        name=symbol,
                        asset_type=AssetType.STOCK,
                        currency="CAD",
                        institution="Questrade",
                        sync_source="QUESTRADE",
                    )
                    db.add(asset)
                    db.flush()
                    existing = asset
                    assets_created += 1

                positions_synced += 1

        db.commit()

    return QuestradeSyncResponse(
        accounts_synced=len(accounts),
        assets_created=assets_created,
        assets_updated=assets_updated,
        positions_synced=positions_synced,
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
            {
                "id": "pluggy",
                "name": "Pluggy",
                "description": "Brazilian Open Finance integration",
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
                "id": "nubank",
                "name": "Nubank",
                "country": "Brazil",
                "type": "bank",
                "export_instructions": "App > Conta > Extrato > Exportar CSV",
                "sample_headers": ["date", "title", "amount", "category"],
            },
            {
                "id": "nubank_investments",
                "name": "Nubank Investimentos",
                "country": "Brazil",
                "type": "brokerage",
                "export_instructions": "App > Investimentos > Extrato > Exportar",
                "sample_headers": ["Data", "Descrição", "Valor", "Tipo", "Ativo"],
            },
            {
                "id": "clear",
                "name": "Clear Investimentos",
                "country": "Brazil",
                "type": "brokerage",
                "export_instructions": "Portal > Relatórios > Notas de Corretagem > Exportar CSV",
                "sample_headers": [
                    "Data Negócio",
                    "C/V",
                    "Código",
                    "Especificação do Título",
                    "Quantidade",
                    "Preço",
                    "Valor Total",
                ],
            },
            {
                "id": "xp",
                "name": "XP Investimentos",
                "country": "Brazil",
                "type": "brokerage",
                "export_instructions": "Portal > Meus Investimentos > Posição > Exportar",
                "sample_headers": [
                    "Data do Negócio",
                    "Código do Ativo",
                    "Tipo de Movimentação",
                    "Quantidade",
                    "Preço Unitário",
                    "Valor Líquido",
                ],
            },
            {
                "id": "b3_cei",
                "name": "B3 CEI (Canal Eletrônico do Investidor)",
                "country": "Brazil",
                "type": "consolidated",
                "export_instructions": "cei.b3.com.br > Extratos e Informativos > Negociação > Exportar",
                "sample_headers": [
                    "Data do Negócio",
                    "Código de Negociação",
                    "Tipo de Movimentação",
                    "Instituição",
                    "Quantidade",
                    "Preço",
                    "Valor",
                ],
                "notes": "Consolidates all Brazilian brokerages in one export",
            },
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
