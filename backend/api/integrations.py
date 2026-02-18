"""API endpoints for third-party integrations (Wise, Questrade, etc.)."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select

from backend.db.session import DbSession
from backend.db.models.asset import Asset, AssetType, SyncSource
from backend.db.models.lot import Lot

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


# ==================== Questrade Integration ====================

class QuestradeConnectRequest(BaseModel):
    """Request to connect or test Questrade (refresh token from my.questrade.com/APIAccess)."""
    refresh_token: str


class QuestradeAccountResponse(BaseModel):
    """Questrade account summary."""
    number: str
    type: str
    status: str
    is_primary: bool
    is_billing: bool
    client_account_type: str


class QuestradePositionResponse(BaseModel):
    """Questrade position (holding)."""
    symbol_id: int
    symbol: str
    open_quantity: Decimal
    current_market_value: Optional[Decimal] = None
    current_price: Optional[Decimal] = None
    average_entry_price: Optional[Decimal] = None
    open_pnl: Optional[Decimal] = None
    closed_pnl: Optional[Decimal] = None


class QuestradeBalanceResponse(BaseModel):
    """Questrade balance per currency."""
    currency: str
    cash: Decimal
    market_value: Decimal
    total_equity: Decimal
    buying_power: Optional[Decimal] = None
    maintenance_excess: Optional[Decimal] = None


@router.post("/questrade/test-connection")
async def test_questrade_connection(request: QuestradeConnectRequest):
    """Test Questrade API connection with provided refresh token."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            accounts = qt.get_accounts()
            if not accounts:
                raise HTTPException(status_code=400, detail="No accounts found")
            primary = next((a for a in accounts if a.is_primary), accounts[0])
            return {
                "status": "connected",
                "accounts_count": len(accounts),
                "primary_account": primary.number,
                "primary_type": primary.type,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.post("/questrade/accounts", response_model=list[QuestradeAccountResponse])
async def get_questrade_accounts(request: QuestradeConnectRequest):
    """Get all Questrade accounts for the authenticated user."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
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
        raise HTTPException(status_code=400, detail=f"Failed to fetch accounts: {str(e)}")


class QuestradePositionsRequest(BaseModel):
    """Request for positions (refresh token + account number)."""
    refresh_token: str
    account_number: str


@router.post("/questrade/positions", response_model=list[QuestradePositionResponse])
async def get_questrade_positions(request: QuestradePositionsRequest):
    """Get positions for a single Questrade account."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            positions = qt.get_positions(request.account_number)
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
        raise HTTPException(status_code=400, detail=f"Failed to fetch positions: {str(e)}")


class QuestradeSyncRequest(BaseModel):
    """Request to sync Questrade positions into Canopy database."""
    refresh_token: str


@router.post("/questrade/sync")
async def sync_questrade_to_canopy(request: QuestradeSyncRequest, db: DbSession):
    """Sync all Questrade accounts and positions into Canopy assets and lots."""
    try:
        from backend.services.questrade_integration import QuestradeIntegrationService

        with QuestradeIntegrationService(request.refresh_token) as qt:
            accounts = qt.get_accounts()
            created_assets = 0
            created_lots = 0
            updated_lots = 0

            for acc in accounts:
                positions = qt.get_positions(acc.number)
                for pos in positions:
                    symbol = (pos.symbol or "").strip().upper()
                    if not symbol:
                        continue
                    price = pos.average_entry_price or pos.current_price or Decimal("0")
                    if price <= 0:
                        price = Decimal("0.01")

                    asset = db.execute(
                        select(Asset).where(Asset.symbol == symbol)
                    ).scalar_one_or_none()
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
                        lot = Lot(
                            asset_id=asset.id,
                            quantity=pos.open_quantity,
                            price_per_unit=price,
                            fees=Decimal("0"),
                            purchase_date=date.today(),
                            account=account_label,
                            notes=f"Synced from Questrade {acc.type}",
                        )
                        db.add(lot)
                        created_lots += 1

            db.commit()
            return {
                "status": "synced",
                "accounts": len(accounts),
                "created_assets": created_assets,
                "created_lots": created_lots,
                "updated_lots": updated_lots,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sync failed: {str(e)}")


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
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


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


# ==================== Integration Status ====================

@router.get("/status")
async def get_integration_status():
    """Get status of all available integrations."""
    return {
        "integrations": [
            {
                "id": "questrade",
                "name": "Questrade",
                "type": "api",
                "status": "available",
                "description": "Canadian discount brokerage. TFSA, RRSP, Margin accounts.",
                "requires_refresh_token": True,
                "supported_features": ["accounts", "positions", "balances", "sync"],
            },
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
