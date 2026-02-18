"""API endpoints for third-party integrations (Wise, etc.)."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from backend.app.config import get_settings
from backend.db.session import DbSession
from backend.db.models.asset import Asset, AssetType
from backend.db.models.transaction import Transaction as TransactionModel

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
                select(TransactionModel.import_id).where(
                    TransactionModel.import_source == "wise"
                )
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


# ==================== Moomoo (Futu) Integration ====================

class MoomooConnectRequest(BaseModel):
    """Request to connect to Moomoo OpenD gateway."""
    host: str = "127.0.0.1"
    port: int = 11111
    rsa_path: Optional[str] = None


class MoomooAccountResponse(BaseModel):
    """Account response from Moomoo."""
    acc_id: int
    acc_type: str
    card_num: str
    currency: str
    market: str
    status: str


class MoomooPositionResponse(BaseModel):
    """Position response from Moomoo."""
    code: str
    name: str
    quantity: float
    cost_price: Optional[float] = None
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    currency: str
    market: str


class MoomooBalanceResponse(BaseModel):
    """Balance response from Moomoo."""
    currency: str
    cash: float
    frozen_cash: float
    market_value: float
    total_assets: float
    available_funds: float


class MoomooQuoteResponse(BaseModel):
    """Market quote response."""
    code: str
    name: str
    last_price: float
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    prev_close: Optional[float] = None
    volume: int
    turnover: float
    change_val: Optional[float] = None
    change_pct: Optional[float] = None
    update_time: str


@router.post("/moomoo/test-connection")
async def test_moomoo_connection(request: MoomooConnectRequest):
    """Test connection to Moomoo OpenD gateway.
    
    The user must have OpenD running locally.
    Download from: https://openapi.futunn.com/
    """
    try:
        from backend.services.moomoo_integration import (
            MoomooIntegrationService,
            MoomooConnectionError,
        )
        
        service = MoomooIntegrationService(
            host=request.host,
            port=request.port,
            rsa_path=request.rsa_path,
        )
        
        if not service.connect():
            raise HTTPException(status_code=400, detail="Failed to connect to OpenD")
        
        status = service.get_connection_status()
        service.close()
        
        return {
            "status": "connected",
            "gateway": f"{request.host}:{request.port}",
            "details": status,
        }
        
    except MoomooConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="futu-api package not installed. Contact administrator."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.post("/moomoo/accounts", response_model=list[MoomooAccountResponse])
async def get_moomoo_accounts(request: MoomooConnectRequest):
    """Get all trading accounts from Moomoo."""
    try:
        from backend.services.moomoo_integration import (
            MoomooIntegrationService,
            MoomooConnectionError,
        )
        
        with MoomooIntegrationService(
            host=request.host,
            port=request.port,
            rsa_path=request.rsa_path,
        ) as moomoo:
            accounts = moomoo.get_accounts()
            return [
                MoomooAccountResponse(
                    acc_id=acc.acc_id,
                    acc_type=acc.acc_type,
                    card_num=acc.card_num,
                    currency=acc.currency,
                    market=acc.market,
                    status=acc.status,
                )
                for acc in accounts
            ]
            
    except MoomooConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch accounts: {str(e)}")


class MoomooPositionsRequest(BaseModel):
    """Request for Moomoo positions."""
    host: str = "127.0.0.1"
    port: int = 11111
    rsa_path: Optional[str] = None
    acc_id: int
    market: str = "US"


@router.post("/moomoo/positions", response_model=list[MoomooPositionResponse])
async def get_moomoo_positions(request: MoomooPositionsRequest):
    """Get positions for a Moomoo account."""
    try:
        from backend.services.moomoo_integration import (
            MoomooIntegrationService,
            MoomooConnectionError,
        )
        
        with MoomooIntegrationService(
            host=request.host,
            port=request.port,
            rsa_path=request.rsa_path,
        ) as moomoo:
            positions = moomoo.get_positions(request.acc_id, request.market)
            return [
                MoomooPositionResponse(
                    code=pos.code,
                    name=pos.name,
                    quantity=float(pos.quantity),
                    cost_price=float(pos.cost_price) if pos.cost_price else None,
                    current_price=float(pos.current_price) if pos.current_price else None,
                    market_value=float(pos.market_value) if pos.market_value else None,
                    profit_loss=float(pos.profit_loss) if pos.profit_loss else None,
                    profit_loss_pct=float(pos.profit_loss_pct) if pos.profit_loss_pct else None,
                    currency=pos.currency,
                    market=pos.market,
                )
                for pos in positions
            ]
            
    except MoomooConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch positions: {str(e)}")


class MoomooBalancesRequest(BaseModel):
    """Request for Moomoo balances."""
    host: str = "127.0.0.1"
    port: int = 11111
    rsa_path: Optional[str] = None
    acc_id: int
    market: str = "US"


@router.post("/moomoo/balances", response_model=list[MoomooBalanceResponse])
async def get_moomoo_balances(request: MoomooBalancesRequest):
    """Get balances for a Moomoo account."""
    try:
        from backend.services.moomoo_integration import (
            MoomooIntegrationService,
            MoomooConnectionError,
        )
        
        with MoomooIntegrationService(
            host=request.host,
            port=request.port,
            rsa_path=request.rsa_path,
        ) as moomoo:
            balances = moomoo.get_balances(request.acc_id, request.market)
            return [
                MoomooBalanceResponse(
                    currency=bal.currency,
                    cash=float(bal.cash),
                    frozen_cash=float(bal.frozen_cash),
                    market_value=float(bal.market_value),
                    total_assets=float(bal.total_assets),
                    available_funds=float(bal.available_funds),
                )
                for bal in balances
            ]
            
    except MoomooConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch balances: {str(e)}")


class MoomooQuoteRequest(BaseModel):
    """Request for Moomoo quotes."""
    host: str = "127.0.0.1"
    port: int = 11111
    codes: list[str]


@router.post("/moomoo/quotes", response_model=list[MoomooQuoteResponse])
async def get_moomoo_quotes(request: MoomooQuoteRequest):
    """Get real-time quotes for securities.
    
    Codes should be in format: "MARKET.SYMBOL" (e.g., "US.AAPL", "HK.00700")
    """
    try:
        from backend.services.moomoo_integration import (
            MoomooIntegrationService,
            MoomooConnectionError,
        )
        
        with MoomooIntegrationService(
            host=request.host,
            port=request.port,
        ) as moomoo:
            quotes = moomoo.get_quote(request.codes)
            return [
                MoomooQuoteResponse(
                    code=q.code,
                    name=q.name,
                    last_price=float(q.last_price),
                    open_price=float(q.open_price) if q.open_price else None,
                    high_price=float(q.high_price) if q.high_price else None,
                    low_price=float(q.low_price) if q.low_price else None,
                    prev_close=float(q.prev_close) if q.prev_close else None,
                    volume=q.volume,
                    turnover=float(q.turnover),
                    change_val=float(q.change_val) if q.change_val else None,
                    change_pct=float(q.change_pct) if q.change_pct else None,
                    update_time=q.update_time,
                )
                for q in quotes
            ]
            
    except MoomooConnectionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch quotes: {str(e)}")


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
                "id": "moomoo",
                "name": "Moomoo (Futu)",
                "type": "gateway",
                "status": "available",
                "description": "US/HK/CN/SG/JP stock trading via local OpenD gateway",
                "requires_gateway": True,
                "gateway_download": "https://openapi.futunn.com/",
                "supported_features": ["accounts", "positions", "balances", "quotes"],
                "supported_markets": ["US", "HK", "CN", "SG", "JP"],
            },
            {
                "id": "csv_import",
                "name": "CSV Import",
                "type": "file",
                "status": "available",
                "description": "Import transactions from CSV exports",
                "supported_formats": [
                    "Nubank", "Clear Investimentos", "XP Investimentos",
                    "RBC Canada", "Wealthsimple", "Schwab", "Wise",
                    "Chase", "Bank of America", "Capital One", "Amex"
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
                "sample_headers": ["Data Negócio", "C/V", "Código", "Especificação do Título", "Quantidade", "Preço", "Valor Total"],
            },
            {
                "id": "xp",
                "name": "XP Investimentos",
                "country": "Brazil",
                "type": "brokerage",
                "export_instructions": "Portal > Meus Investimentos > Posição > Exportar",
                "sample_headers": ["Data do Negócio", "Código do Ativo", "Tipo de Movimentação", "Quantidade", "Preço Unitário", "Valor Líquido"],
            },
            {
                "id": "b3_cei",
                "name": "B3 CEI (Canal Eletrônico do Investidor)",
                "country": "Brazil",
                "type": "consolidated",
                "export_instructions": "cei.b3.com.br > Extratos e Informativos > Negociação > Exportar",
                "sample_headers": ["Data do Negócio", "Código de Negociação", "Tipo de Movimentação", "Instituição", "Quantidade", "Preço", "Valor"],
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
                "sample_headers": ["Date", "Transaction Type", "Symbol", "Quantity", "Price", "Market Value", "Currency"],
            },
            {
                "id": "schwab",
                "name": "Charles Schwab",
                "country": "USA",
                "type": "brokerage",
                "export_instructions": "Accounts > History > Export",
                "sample_headers": ["Date", "Action", "Symbol", "Description", "Quantity", "Price", "Fees & Comm", "Amount"],
            },
            {
                "id": "wise",
                "name": "Wise",
                "country": "Global",
                "type": "bank",
                "export_instructions": "Account > Statement > Download CSV",
                "sample_headers": ["Date", "Description", "Amount", "Currency", "Running Balance", "TransferWise ID"],
                "notes": "Also supports direct API integration",
            },
        ],
    }
