"""Amex Canada monthly statement CSV (website export) — synthetic rows only."""

from datetime import datetime

from backend.models.csv_import import BankFormat, CSVImportConfig
from backend.services.csv_parser import CSVParserService

# Minimal valid rows: same column layout as production export, no real PII
SAMPLE = """Date,Date Processed,Description,Card Member,Account #,Amount,Foreign Spend Amount,Commission,Exchange Rate,Additional Information,Merchant,Address,City / Province,Postal Code,Country,Reference
10 Apr 2026,10 Apr 2026,COFFEE SHOP           TORONTO,MEMBER A,-52003,5.25,,,,,COFFEE SHOP           TORONTO,1 MAIN ST,"TORONTO
ON",M5V 1A1,CANADA,'REF1'
12 Apr 2026,12 Apr 2026,REFUND MERCHANT       TORONTO,MEMBER A,-52003,-5.25,,,,,REFUND MERCHANT       TORONTO,1 MAIN ST,"TORONTO
ON",M5V 1A1,CANADA,'REF2'
"""


def test_detect_amex_monthly_ca():
    svc = CSVParserService()
    headers = [
        "Date",
        "Date Processed",
        "Description",
        "Card Member",
        "Account #",
        "Amount",
        "Foreign Spend Amount",
        "Commission",
        "Exchange Rate",
        "Additional Information",
        "Merchant",
        "Address",
        "City / Province",
        "Postal Code",
        "Country",
        "Reference",
    ]
    assert svc.detect_bank_format(headers) == BankFormat.AMEX_MONTHLY_STATEMENT_CA


def test_parse_amex_monthly_charge_and_refund():
    svc = CSVParserService()
    mapping = svc.BANK_FORMATS[BankFormat.AMEX_MONTHLY_STATEMENT_CA]
    config = CSVImportConfig(
        bank_format=BankFormat.AMEX_MONTHLY_STATEMENT_CA,
        field_mapping=mapping,
        default_currency="CAD",
    )
    preview = svc.parse_csv_file(SAMPLE, config, existing_transactions=[])
    assert preview.total_rows == 2
    assert preview.valid_rows == 2
    a, b = preview.transactions
    assert a.description.startswith("COFFEE")
    assert a.amount == 5.25
    assert a.type == "expense"
    assert a.date == datetime(2026, 4, 10)
    assert a.account == "-52003"
    assert a.merchant and "COFFEE" in (a.merchant or "")
    assert b.type == "income"
    assert b.amount == 5.25
