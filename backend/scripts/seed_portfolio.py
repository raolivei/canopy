"""Seed script to populate Canopy with Rafael's portfolio data.

Canopy - Personal Finance Platform

This script imports:
- 40+ accounts across Canada, USA, and Brazil
- Historical snapshots from Sep 2024 to present
- Real estate (apartment 50% with Alex)
- Liabilities (credit cards, car loan)
- Crypto (both by coin and by platform)

Usage:
    python -m backend.scripts.seed_portfolio
"""

from datetime import date, datetime
from decimal import Decimal
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.db.models import (
    Asset,
    AssetType,
    Lot,
    PortfolioSnapshot,
    SnapshotHolding,
    RealEstateProperty,
    RealEstatePaymentSeries,
    RealEstatePayment,
    Liability,
    LiabilityBalanceHistory,
)


# =============================================================================
# ACCOUNT DEFINITIONS
# =============================================================================

# Canada (CAD) Accounts
CANADA_ACCOUNTS = [
    # RBC Accounts
    {
        "symbol": "RBC_CHEQUING",
        "name": "RBC Royal Bank Chequings",
        "asset_type": AssetType.BANK_CHECKING,
        "currency": "CAD",
        "institution": "RBC",
        "country": "CA",
    },
    {
        "symbol": "RBC_SAVINGS",
        "name": "RBC Royal Bank Savings",
        "asset_type": AssetType.BANK_SAVINGS,
        "currency": "CAD",
        "institution": "RBC",
        "country": "CA",
    },
    {
        "symbol": "RBC_TFSA",
        "name": "RBC TFSA",
        "asset_type": AssetType.RETIREMENT_TFSA,
        "currency": "CAD",
        "institution": "RBC",
        "country": "CA",
    },
    {
        "symbol": "RBC_US_CHECKING",
        "name": "RBC US Checking",
        "asset_type": AssetType.BANK_CHECKING,
        "currency": "USD",
        "institution": "RBC",
        "country": "CA",
    },
    # Wealthsimple Accounts
    {
        "symbol": "WS_RRSP",
        "name": "Wealthsimple RRSP",
        "asset_type": AssetType.RETIREMENT_RRSP,
        "currency": "CAD",
        "institution": "Wealthsimple",
        "country": "CA",
        "sync_source": "WEALTHSIMPLE",
    },
    {
        "symbol": "WS_TFSA",
        "name": "Wealthsimple TFSA",
        "asset_type": AssetType.RETIREMENT_TFSA,
        "currency": "CAD",
        "institution": "Wealthsimple",
        "country": "CA",
        "sync_source": "WEALTHSIMPLE",
    },
    {
        "symbol": "WS_FHSA",
        "name": "Wealthsimple FHSA",
        "asset_type": AssetType.RETIREMENT_FHSA,
        "currency": "CAD",
        "institution": "Wealthsimple",
        "country": "CA",
        "sync_source": "WEALTHSIMPLE",
    },
    {
        "symbol": "WS_CHEQUING",
        "name": "Wealthsimple Chequing",
        "asset_type": AssetType.BANK_CHECKING,
        "currency": "CAD",
        "institution": "Wealthsimple",
        "country": "CA",
        "sync_source": "WEALTHSIMPLE",
    },
    {
        "symbol": "WS_DIRECT_INDEX",
        "name": "Wealthsimple Direct Indexing",
        "asset_type": AssetType.ETF,
        "currency": "CAD",
        "institution": "Wealthsimple",
        "country": "CA",
        "sync_source": "WEALTHSIMPLE",
    },
    # CanadaLife
    {
        "symbol": "CL_RRSP",
        "name": "CanadaLife RRSP",
        "asset_type": AssetType.RETIREMENT_RRSP,
        "currency": "CAD",
        "institution": "CanadaLife",
        "country": "CA",
    },
    {
        "symbol": "CL_DPSP",
        "name": "CanadaLife DPSP",
        "asset_type": AssetType.RETIREMENT_DPSP,
        "currency": "CAD",
        "institution": "CanadaLife",
        "country": "CA",
    },
    # Brokerage accounts
    {
        "symbol": "MOOMOO_CAD",
        "name": "Moomoo",
        "asset_type": AssetType.STOCK,
        "currency": "CAD",
        "institution": "Moomoo",
        "country": "CA",
        "sync_source": "MOOMOO",
    },
    {
        "symbol": "QUESTRADE",
        "name": "Questrade",
        "asset_type": AssetType.STOCK,
        "currency": "CAD",
        "institution": "Questrade",
        "country": "CA",
        "sync_source": "QUESTRADE",
    },
    {
        "symbol": "WISE_CAD",
        "name": "Wise",
        "asset_type": AssetType.BANK_ACCOUNT,
        "currency": "CAD",
        "institution": "Wise",
        "country": "CA",
        "sync_source": "WISE",
    },
]

# USA (USD) Accounts
USA_ACCOUNTS = [
    {
        "symbol": "SCHWAB",
        "name": "Schwab (former TD Ameritrade)",
        "asset_type": AssetType.STOCK,
        "currency": "USD",
        "institution": "Schwab",
        "country": "US",
    },
    {
        "symbol": "SPACEX_SHARES",
        "name": "SpaceX Shares (15 shares via Alex)",
        "asset_type": AssetType.PRIVATE_EQUITY,
        "currency": "USD",
        "institution": "SpaceX",
        "country": "US",
        "notes": "15 shares purchased via Alex's ESPP in April 2024. 100% owned by Rafael.",
    },
]

# Brazil (BRL) Accounts
BRAZIL_ACCOUNTS = [
    {
        "symbol": "NUBANK_CC",
        "name": "Nubank Conta Corrente",
        "asset_type": AssetType.BANK_ACCOUNT,
        "currency": "BRL",
        "institution": "Nubank",
        "country": "BR",
    },
    {
        "symbol": "NUBANK_INVEST",
        "name": "Nubank Investimentos",
        "asset_type": AssetType.STOCK,
        "currency": "BRL",
        "institution": "Nubank",
        "country": "BR",
    },
    {
        "symbol": "CLEAR_ATIVOS",
        "name": "Clear Investimentos",
        "asset_type": AssetType.STOCK,
        "currency": "BRL",
        "institution": "Clear",
        "country": "BR",
    },
    {
        "symbol": "XP_RV",
        "name": "XP Investimentos",
        "asset_type": AssetType.STOCK,
        "currency": "BRL",
        "institution": "XP",
        "country": "BR",
    },
    {
        "symbol": "URBEME",
        "name": "URBE.ME",
        "asset_type": AssetType.CROWDFUNDING,
        "currency": "BRL",
        "institution": "URBE.ME",
        "country": "BR",
        "notes": "Real estate crowdfunding platform",
    },
    {
        "symbol": "SANTANDER_BR",
        "name": "Santander C/C e Poupança",
        "asset_type": AssetType.BANK_ACCOUNT,
        "currency": "BRL",
        "institution": "Santander",
        "country": "BR",
    },
]

# Crypto Accounts (by platform)
CRYPTO_PLATFORM_ACCOUNTS = [
    {
        "symbol": "LEDGER_BTC",
        "name": "Ledger (BTC)",
        "asset_type": AssetType.CRYPTO,
        "currency": "BTC",
        "institution": "Ledger",
        "country": None,
    },
    {
        "symbol": "COINBASE_BTC",
        "name": "Coinbase (BTC)",
        "asset_type": AssetType.CRYPTO,
        "currency": "BTC",
        "institution": "Coinbase",
        "country": None,
    },
    {
        "symbol": "COINBASE_ETH",
        "name": "Coinbase (ETH)",
        "asset_type": AssetType.CRYPTO,
        "currency": "ETH",
        "institution": "Coinbase",
        "country": None,
    },
    {
        "symbol": "KUCOIN",
        "name": "KuCoin",
        "asset_type": AssetType.CRYPTO,
        "currency": "USD",
        "institution": "KuCoin",
        "country": None,
    },
]

# Crypto Aggregated (by coin - for alternative view)
CRYPTO_AGGREGATED = [
    {
        "symbol": "BTC_TOTAL",
        "name": "Bitcoin (Total)",
        "asset_type": AssetType.CRYPTO,
        "currency": "BTC",
        "institution": None,
        "country": None,
        "notes": "Aggregated BTC across all wallets: Ledger, Coinbase, etc.",
    },
    {
        "symbol": "ETH_TOTAL",
        "name": "Ethereum (Total)",
        "asset_type": AssetType.CRYPTO,
        "currency": "ETH",
        "institution": None,
        "country": None,
        "notes": "Aggregated ETH across all wallets: Coinbase, Ledger, etc.",
    },
]

# =============================================================================
# LIABILITY DEFINITIONS
# =============================================================================

LIABILITIES = [
    # Car Loan
    {
        "name": "RBC Car Loan",
        "institution": "RBC",
        "liability_type": "car_loan",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("28521.00"),
        "apr": Decimal("0.0699"),  # 6.99% typical auto loan rate
        "loan_term_months": 60,
    },
    # Credit Cards
    {
        "name": "RBC VISA 7192",
        "institution": "RBC",
        "account_number_last4": "7192",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("27016.00"),
        "credit_limit": Decimal("30000.00"),
        "apr": Decimal("0.1999"),
    },
    {
        "name": "Amazon.ca MBNA Mastercard",
        "institution": "MBNA",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("6868.00"),
        "apr": Decimal("0.1999"),
    },
    {
        "name": "RBC WestJet Mastercard",
        "institution": "RBC",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("908.00"),
        "apr": Decimal("0.1999"),
        "rewards_program": "WestJet Dollars",
        "annual_fee": Decimal("119.00"),
    },
    {
        "name": "Wealthsimple Credit Card",
        "institution": "Wealthsimple",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("951.00"),
        "apr": Decimal("0.1999"),
    },
    {
        "name": "Scotiabank Momentum VISA Infinite",
        "institution": "Scotiabank",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("0.00"),  # Has positive balance (rewards)
        "apr": Decimal("0.2099"),
        "annual_fee": Decimal("120.00"),
    },
    {
        "name": "AMEX Cobalt",
        "institution": "American Express",
        "liability_type": "credit_card",
        "currency": "CAD",
        "country": "CA",
        "current_balance": Decimal("0.00"),  # Has positive balance (rewards)
        "apr": Decimal("0.2099"),
        "annual_fee": Decimal("156.00"),
        "rewards_program": "Amex Points",
    },
]

# =============================================================================
# HISTORICAL SNAPSHOTS
# Based on the user's CSV data from Sep 2024 to present
# =============================================================================

HISTORICAL_SNAPSHOTS = [
    # Jan 2025 snapshot (most recent complete data from CSV)
    {
        "date": date(2025, 1, 19),
        "balances": {
            # Canada (CAD)
            "RBC_CHEQUING": Decimal("3518.00"),
            "RBC_TFSA": Decimal("510.00"),
            "CL_RRSP": Decimal("59129.00"),
            "WS_RRSP": Decimal("84551.00"),
            "WS_TFSA": Decimal("2646.00"),
            "WS_FHSA": Decimal("3435.00"),
            # USA (USD)
            "SCHWAB": Decimal("10244.07"),
            "RBC_US_CHECKING": Decimal("239.93"),
            # Brazil (BRL)
            "SANTANDER_BR": Decimal("125.00"),
            "NUBANK_CC": Decimal("7865.00"),
            "NUBANK_INVEST": Decimal("33428.00"),
            "CLEAR_ATIVOS": Decimal("972.00"),
            "XP_RV": Decimal("68807.00"),
            "URBEME": Decimal("85797.00"),
            # Crypto (USD)
            "KUCOIN": Decimal("6278.42"),
            "COINBASE_BTC": Decimal("307.63"),
            "COINBASE_ETH": Decimal("23999.70"),
            "LEDGER_BTC": Decimal("48829.03"),
        },
    },
    # Oct 2024 snapshot
    {
        "date": date(2024, 10, 15),
        "balances": {
            "RBC_CHEQUING": Decimal("3056.00"),
            "RBC_TFSA": Decimal("509.00"),
            "CL_RRSP": Decimal("53241.00"),
            "WS_RRSP": Decimal("78547.00"),
            "WS_TFSA": Decimal("8566.00"),
            "WS_FHSA": Decimal("3045.00"),
            "SCHWAB": Decimal("17334.12"),
            "RBC_US_CHECKING": Decimal("750.00"),
            "SANTANDER_BR": Decimal("63.00"),
            "NUBANK_CC": Decimal("9091.00"),
            "NUBANK_INVEST": Decimal("20753.00"),
            "XP_RV": Decimal("65759.00"),
            "URBEME": Decimal("65630.00"),
            "LEDGER_BTC": Decimal("53708.95"),
            "COINBASE_ETH": Decimal("4461.76"),
        },
    },
    # May 2025 snapshot (latest from CSV)
    {
        "date": date(2025, 5, 15),
        "balances": {
            "RBC_TFSA": Decimal("510.00"),
            "CL_RRSP": Decimal("4982.00"),
            "CL_DPSP": Decimal("27677.00"),
            "WS_RRSP": Decimal("124509.00"),
            "WS_TFSA": Decimal("8065.00"),
            "WS_FHSA": Decimal("9675.00"),
            "WS_CHEQUING": Decimal("86.00"),
            "SCHWAB": Decimal("10436.82"),
            "RBC_US_CHECKING": Decimal("102.55"),
            "SPACEX_SHARES": Decimal("2775.00"),
            "SANTANDER_BR": Decimal("193.00"),
            "NUBANK_CC": Decimal("26003.00"),
            "NUBANK_INVEST": Decimal("63976.00"),
            "CLEAR_ATIVOS": Decimal("14690.00"),
            "XP_RV": Decimal("35037.00"),
            "URBEME": Decimal("84218.00"),
            "KUCOIN": Decimal("5462.31"),
            "COINBASE_BTC": Decimal("282.76"),
            "COINBASE_ETH": Decimal("13226.33"),
            "LEDGER_BTC": Decimal("44762.34"),
        },
    },
    # Latest snapshot (from most recent CSV row)
    {
        "date": date(2025, 12, 15),  # Approximate date
        "balances": {
            "RBC_CHEQUING": Decimal("1223.00"),
            "RBC_TFSA": Decimal("513.00"),
            "CL_RRSP": Decimal("15724.00"),
            "CL_DPSP": Decimal("38662.00"),
            "WS_RRSP": Decimal("150053.00"),
            "WS_TFSA": Decimal("2920.00"),
            "WS_FHSA": Decimal("17880.00"),
            "WS_CHEQUING": Decimal("1808.00"),
            "WS_DIRECT_INDEX": Decimal("976.00"),
            "MOOMOO_CAD": Decimal("6775.00"),
            "QUESTRADE": Decimal("153.00"),
            "WISE_CAD": Decimal("318.00"),
            "SCHWAB": Decimal("11267.96"),
            "RBC_US_CHECKING": Decimal("7.76"),
            "SPACEX_SHARES": Decimal("3180.00"),
            "SANTANDER_BR": Decimal("8.00"),
            "NUBANK_CC": Decimal("26267.00"),
            "NUBANK_INVEST": Decimal("14587.00"),
            "CLEAR_ATIVOS": Decimal("36068.00"),
            "XP_RV": Decimal("36312.00"),
            "URBEME": Decimal("56237.00"),
            "KUCOIN": Decimal("3464.70"),
            "COINBASE_BTC": Decimal("334.00"),
            "COINBASE_ETH": Decimal("17935.00"),
            "LEDGER_BTC": Decimal("36422.92"),
        },
    },
]

# =============================================================================
# APARTMENT DATA (50% ownership with Alex)
# =============================================================================

APARTMENT_DATA = {
    "name": "Apartamento Porto Alegre",
    "city": "Porto Alegre",
    "state": "RS",
    "country": "BR",
    "currency": "BRL",
    "total_contract_value": Decimal("380417.00"),
    "ownership_percentage": Decimal("0.5"),  # 50%
    "partner_name": "Alex",
    "partner_ownership_percentage": Decimal("0.5"),
    "purchase_date": date(2024, 2, 20),
    "expected_delivery_date": date(2027, 4, 30),
    "payment_series": [
        {
            "name": "ATO",
            "frequency": "one_time",
            "total_installments": 1,
            "nominal_amount": Decimal("40000.00"),
            "start_date": date(2024, 2, 20),
            "status": "paid",
        },
        {
            "name": "SINAL",
            "frequency": "one_time",
            "total_installments": 2,
            "nominal_amount": Decimal("20000.00"),
            "start_date": date(2024, 3, 20),
            "status": "paid",
        },
        {
            "name": "MENSAIS 2024",
            "frequency": "monthly",
            "total_installments": 7,
            "nominal_amount": Decimal("14000.00"),
            "start_date": date(2024, 6, 20),
            "status": "paid",
        },
        {
            "name": "MENSAIS 2025",
            "frequency": "monthly",
            "total_installments": 12,
            "nominal_amount": Decimal("24000.00"),
            "start_date": date(2025, 1, 20),
            "status": "ongoing",
        },
        {
            "name": "MENSAIS 2026",
            "frequency": "monthly",
            "total_installments": 10,
            "nominal_amount": Decimal("20000.00"),
            "start_date": date(2026, 1, 20),
            "status": "not_started",
        },
        {
            "name": "SEMESTRAIS",
            "frequency": "semi_annual",
            "total_installments": 4,
            "nominal_amount": Decimal("50000.00"),
            "start_date": date(2024, 7, 20),
            "status": "ongoing",
        },
        {
            "name": "UNICA SET/2026",
            "frequency": "one_time",
            "total_installments": 1,
            "nominal_amount": Decimal("42000.00"),
            "start_date": date(2026, 9, 20),
            "status": "not_started",
        },
        {
            "name": "UNICA ABR/2027",
            "frequency": "one_time",
            "total_installments": 1,
            "nominal_amount": Decimal("417.00"),
            "start_date": date(2027, 4, 20),
            "status": "not_started",
        },
    ],
}


# =============================================================================
# SEEDING FUNCTIONS
# =============================================================================

def create_assets(db: Session) -> dict[str, Asset]:
    """Create all asset records."""
    print("Creating assets...")
    assets = {}
    
    all_accounts = (
        CANADA_ACCOUNTS + 
        USA_ACCOUNTS + 
        BRAZIL_ACCOUNTS + 
        CRYPTO_PLATFORM_ACCOUNTS +
        CRYPTO_AGGREGATED
    )
    
    for account in all_accounts:
        asset = Asset(
            symbol=account["symbol"],
            name=account["name"],
            asset_type=account["asset_type"],
            currency=account["currency"],
            institution=account.get("institution"),
            country=account.get("country"),
            sync_source=account.get("sync_source", "MANUAL"),
            notes=account.get("notes"),
        )
        db.add(asset)
        assets[account["symbol"]] = asset
        print(f"  Created: {account['symbol']} - {account['name']}")
    
    db.flush()
    print(f"Created {len(assets)} assets.\n")
    return assets


def create_liabilities(db: Session) -> list[Liability]:
    """Create all liability records."""
    print("Creating liabilities...")
    liabilities = []
    
    for liability_data in LIABILITIES:
        liability = Liability(
            name=liability_data["name"],
            institution=liability_data["institution"],
            account_number_last4=liability_data.get("account_number_last4"),
            liability_type=liability_data["liability_type"],
            currency=liability_data["currency"],
            country=liability_data["country"],
            current_balance=liability_data["current_balance"],
            apr=liability_data.get("apr"),
            credit_limit=liability_data.get("credit_limit"),
            loan_term_months=liability_data.get("loan_term_months"),
            rewards_program=liability_data.get("rewards_program"),
            annual_fee=liability_data.get("annual_fee"),
            balance_updated_at=datetime.now(),
        )
        db.add(liability)
        liabilities.append(liability)
        print(f"  Created: {liability_data['name']} - Balance: {liability_data['currency']} {liability_data['current_balance']}")
    
    db.flush()
    print(f"Created {len(liabilities)} liabilities.\n")
    return liabilities


def create_real_estate(db: Session) -> RealEstateProperty:
    """Create the apartment property with payment schedule."""
    print("Creating real estate property...")
    
    property_obj = RealEstateProperty(
        name=APARTMENT_DATA["name"],
        city=APARTMENT_DATA["city"],
        state=APARTMENT_DATA["state"],
        country=APARTMENT_DATA["country"],
        currency=APARTMENT_DATA["currency"],
        total_contract_value=APARTMENT_DATA["total_contract_value"],
        ownership_percentage=APARTMENT_DATA["ownership_percentage"],
        partner_name=APARTMENT_DATA["partner_name"],
        partner_ownership_percentage=APARTMENT_DATA["partner_ownership_percentage"],
        purchase_date=APARTMENT_DATA["purchase_date"],
        expected_delivery_date=APARTMENT_DATA["expected_delivery_date"],
        notes="50/50 partnership with Alex. Under construction.",
    )
    db.add(property_obj)
    db.flush()
    
    print(f"  Created: {APARTMENT_DATA['name']}")
    print(f"    Total value: BRL {APARTMENT_DATA['total_contract_value']:,.2f}")
    print(f"    Your share (50%): BRL {APARTMENT_DATA['total_contract_value'] * Decimal('0.5'):,.2f}")
    
    # Create payment series
    print("  Creating payment series...")
    for series_data in APARTMENT_DATA["payment_series"]:
        series = RealEstatePaymentSeries(
            property_id=property_obj.id,
            name=series_data["name"],
            frequency=series_data["frequency"],
            total_installments=series_data["total_installments"],
            nominal_amount_per_installment=series_data["nominal_amount"],
            start_date=series_data["start_date"],
            status=series_data["status"],
        )
        db.add(series)
        print(f"    {series_data['name']}: {series_data['total_installments']}x BRL {series_data['nominal_amount']:,.2f} ({series_data['status']})")
    
    db.flush()
    print()
    return property_obj


def create_historical_snapshots(db: Session, assets: dict[str, Asset]) -> list[PortfolioSnapshot]:
    """Create historical portfolio snapshots."""
    print("Creating historical snapshots...")
    snapshots = []
    
    for snapshot_data in HISTORICAL_SNAPSHOTS:
        # Calculate total value
        total_value = sum(snapshot_data["balances"].values())
        
        snapshot = PortfolioSnapshot(
            snapshot_date=snapshot_data["date"],
            total_value=total_value,
            total_cost_basis=Decimal("0"),  # Would need actual cost basis data
        )
        db.add(snapshot)
        db.flush()
        
        # Create holdings for this snapshot
        for symbol, balance in snapshot_data["balances"].items():
            if symbol in assets:
                holding = SnapshotHolding(
                    snapshot_id=snapshot.id,
                    asset_id=assets[symbol].id,
                    quantity=Decimal("1"),  # Simplified - actual quantity would vary
                    market_value=balance,
                    cost_basis=Decimal("0"),
                    price_at_snapshot=balance,  # Price equals balance for quantity=1
                )
                db.add(holding)
                
                # Also update the asset's current price to the most recent balance
                assets[symbol].current_price = balance
                assets[symbol].price_updated_at = datetime.now()
        
        snapshots.append(snapshot)
        print(f"  {snapshot_data['date']}: Total value recorded")
    
    db.flush()
    print(f"Created {len(snapshots)} historical snapshots.\n")
    return snapshots


def seed_database():
    """Main function to seed the database with all data."""
    print("=" * 60)
    print("Canopy - Database Seeding")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    try:
        # Create all records
        assets = create_assets(db)
        liabilities = create_liabilities(db)
        real_estate = create_real_estate(db)
        snapshots = create_historical_snapshots(db, assets)
        
        # Commit all changes
        db.commit()
        
        print("=" * 60)
        print("Seeding complete!")
        print("=" * 60)
        print(f"  Assets created: {len(assets)}")
        print(f"  Liabilities created: {len(liabilities)}")
        print(f"  Real estate properties: 1")
        print(f"  Historical snapshots: {len(snapshots)}")
        print()
        
        # Summary
        total_liabilities = sum(l.current_balance for l in liabilities)
        print("Liability Summary:")
        print(f"  Total liabilities: CAD {total_liabilities:,.2f}")
        print()
        
        print("Real Estate Summary:")
        print(f"  Property: {real_estate.name}")
        print(f"  Your equity: {real_estate.equity_percentage:.1f}%")
        print(f"  Total paid (your share): BRL {real_estate.total_paid:,.2f}")
        print(f"  Remaining (your share): BRL {real_estate.total_remaining:,.2f}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


def clear_database():
    """Clear all data from the database (use with caution)."""
    print("Clearing database...")
    db = SessionLocal()
    try:
        # Delete in reverse order of dependencies
        db.query(SnapshotHolding).delete()
        db.query(PortfolioSnapshot).delete()
        db.query(LiabilityPayment).delete()
        db.query(LiabilityBalanceHistory).delete()
        db.query(Liability).delete()
        db.query(RealEstatePayment).delete()
        db.query(RealEstatePaymentSeries).delete()
        db.query(RealEstateProperty).delete()
        db.query(Lot).delete()
        db.query(Asset).delete()
        db.commit()
        print("Database cleared.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed Canopy database")
    parser.add_argument(
        "--clear", 
        action="store_true", 
        help="Clear all data before seeding"
    )
    parser.add_argument(
        "--clear-only",
        action="store_true",
        help="Only clear the database, don't seed"
    )
    
    args = parser.parse_args()
    
    if args.clear_only:
        clear_database()
    elif args.clear:
        clear_database()
        seed_database()
    else:
        seed_database()
