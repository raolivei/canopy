"""Amex Canada Year-End Summary CSV preset and detection."""

from datetime import datetime

from backend.models.csv_import import BankFormat, CSVImportConfig
from backend.services.csv_parser import CSVParserService


SAMPLE_CSV = """Category,Card Member,Account Number,Sub-Category,Date,Month-Billed,Transaction,Charges $,Credits $
Merchandise,Member A,*****52003,Electronics,14/12/2025,Dec 2025,SHOP EXAMPLE,25.50,
Merchandise,Member A,*****52003,Electronics,15/12/2025,Dec 2025,REFUND EXAMPLE,,10.00
Airline,Member B,*****51013,Airlines,01/01/2025,Jan 2025,CARRIER X,100.00,
,,,,,,,,
"""


def test_detect_amex_year_end_summary():
    svc = CSVParserService()
    headers = [
        "Category",
        "Card Member",
        "Account Number",
        "Sub-Category",
        "Date",
        "Month-Billed",
        "Transaction",
        "Charges $",
        "Credits $",
    ]
    assert svc.detect_bank_format(headers) == BankFormat.AMEX_YEAR_END_SUMMARY


def test_parse_amex_year_end_summary_rows():
    svc = CSVParserService()
    mapping = svc.BANK_FORMATS[BankFormat.AMEX_YEAR_END_SUMMARY]
    config = CSVImportConfig(
        bank_format=BankFormat.AMEX_YEAR_END_SUMMARY,
        field_mapping=mapping,
        default_currency="CAD",
    )
    preview = svc.parse_csv_file(SAMPLE_CSV, config, existing_transactions=[])

    assert preview.total_rows == 4
    txs = preview.transactions
    assert txs[0].description == "SHOP EXAMPLE"
    assert txs[0].amount == 25.50
    assert txs[0].type == "expense"
    assert txs[0].category == "Merchandise"
    assert txs[0].notes == "Electronics"
    assert txs[0].account == "*****52003"
    assert txs[0].date == datetime(2025, 12, 14)

    assert txs[1].description == "REFUND EXAMPLE"
    assert txs[1].amount == 10.00
    assert txs[1].type == "income"

    assert txs[2].description == "CARRIER X"
    assert txs[2].amount == 100.00
    assert txs[2].account == "*****51013"

    assert txs[3].has_error is True


def test_both_charge_and_credit_prefers_charge():
    """If both columns have values, debit branch wins (same as Capital One-style split)."""
    svc = CSVParserService()
    mapping = svc.BANK_FORMATS[BankFormat.AMEX_YEAR_END_SUMMARY]
    config = CSVImportConfig(
        bank_format=BankFormat.AMEX_YEAR_END_SUMMARY,
        field_mapping=mapping,
        default_currency="CAD",
    )
    csv_two = """Category,Card Member,Account Number,Sub-Category,Date,Month-Billed,Transaction,Charges $,Credits $
Test,A,*****1,Sub,02/06/2025,Jun 2025,DUAL,5.00,3.00
"""
    preview = svc.parse_csv_file(csv_two, config, existing_transactions=[])
    assert len(preview.transactions) == 1
    assert preview.transactions[0].amount == 5.0
    assert preview.transactions[0].type == "expense"
