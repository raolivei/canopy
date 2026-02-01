"""API endpoints for third-party integrations (Wise, etc.)."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

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
