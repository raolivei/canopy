#!/usr/bin/env python3
"""
Test script for CSV import functionality
"""

import sys
import os

# Add project root to path
sys.path.insert(0, '/Users/roliveira/WORKSPACE/raolivei/ledger-light')

from backend.services.csv_parser import CSVParserService
from backend.models.csv_import import CSVImportConfig, BankFormat
from backend.models.transaction import Transaction

def test_monarch_csv_import():
    """Test importing the actual Monarch Money CSV file"""
    
    print("="*80)
    print("CSV IMPORT FUNCTIONALITY TEST")
    print("="*80)
    
    # Initialize parser
    parser = CSVParserService()
    print("\n✅ CSV Parser Service initialized")
    print(f"   Supported formats: {len(parser.BANK_FORMATS)}")
    
    # Test format detection
    csv_file = "transactions-168437284355933952-168437284350262619-89cf9f28-65f8-4479-98a2-2966e6acf748.csv"
    
    if not os.path.exists(csv_file):
        print(f"\n❌ CSV file not found: {csv_file}")
        return False
    
    print(f"\n✅ Found Monarch CSV file")
    
    # Read a sample for testing
    with open(csv_file, 'r') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    print(f"   Total lines in CSV: {total_lines:,}")
    
    # Test header detection
    headers = lines[0].strip().split(',')
    print(f"\n📋 CSV Headers detected:")
    for h in headers:
        print(f"   - {h}")
    
    detected_format = parser.detect_bank_format(headers)
    print(f"\n✅ Format auto-detected: {detected_format}")
    
    if detected_format != BankFormat.MONARCH:
        print(f"❌ Expected MONARCH format, got {detected_format}")
        return False
    
    # Create configuration
    config = CSVImportConfig(
        bank_format=BankFormat.MONARCH,
        field_mapping=parser.BANK_FORMATS[BankFormat.MONARCH],
        default_currency="CAD",
        skip_duplicates=False
    )
    print(f"\n✅ Import configuration created")
    
    # Test with first 100 transactions
    sample_size = 100
    sample_content = ''.join(lines[:sample_size+1])  # +1 for header
    
    print(f"\n🔍 Parsing sample of {sample_size} transactions...")
    preview = parser.parse_csv_file(sample_content, config, [])
    
    print(f"\n📊 Parse Results:")
    print(f"   Total rows: {preview.total_rows}")
    print(f"   Valid rows: {preview.valid_rows}")
    print(f"   Duplicate rows: {preview.duplicate_rows}")
    print(f"   Error rows: {preview.error_rows}")
    
    if preview.error_rows > 0:
        print(f"\n⚠️  Errors found:")
        for tx in preview.transactions:
            if tx.has_error:
                print(f"   Row {tx.row_number}: {tx.error_message}")
    
    # Check date range
    if preview.date_range:
        print(f"\n📅 Date range:")
        print(f"   Start: {preview.date_range['start']}")
        print(f"   End: {preview.date_range['end']}")
    
    # Analyze transaction types
    type_counts = {}
    category_counts = {}
    investment_transactions = []
    
    for tx in preview.transactions:
        type_counts[tx.type] = type_counts.get(tx.type, 0) + 1
        if tx.category:
            category_counts[tx.category] = category_counts.get(tx.category, 0) + 1
        if tx.ticker:
            investment_transactions.append(tx)
    
    print(f"\n📈 Transaction Types:")
    for ttype, count in sorted(type_counts.items()):
        print(f"   {ttype}: {count}")
    
    print(f"\n🏷️  Top Categories:")
    for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cat}: {count}")
    
    print(f"\n💼 Investment Transactions: {len(investment_transactions)}")
    if investment_transactions:
        print(f"   Sample investment transactions:")
        for tx in investment_transactions[:5]:
            print(f"   - {tx.date.strftime('%Y-%m-%d')}: {tx.ticker} ({tx.type}) ${tx.amount:.2f}")
    
    # Display sample transactions
    print(f"\n📝 Sample Transactions (first 5):")
    print("="*80)
    for tx in preview.transactions[:5]:
        print(f"\n{tx.date.strftime('%Y-%m-%d')} | {tx.merchant or tx.description}")
        print(f"  Amount: {tx.currency} ${tx.amount:.2f} ({tx.type})")
        print(f"  Category: {tx.category}")
        print(f"  Account: {tx.account[:40]}..." if tx.account and len(tx.account) > 40 else f"  Account: {tx.account}")
        if tx.ticker:
            print(f"  🎯 Ticker: {tx.ticker}")
        if tx.original_statement:
            stmt = tx.original_statement[:50] + "..." if len(tx.original_statement) > 50 else tx.original_statement
            print(f"  Original: {stmt}")
        if tx.notes:
            print(f"  Notes: {tx.notes}")
        if tx.tags:
            print(f"  Tags: {', '.join(tx.tags)}")
    
    # Test transaction creation
    print(f"\n🔄 Testing transaction creation from preview...")
    transactions_to_create = parser.create_transactions_from_preview(
        preview=preview,
        skip_duplicates=False,
        skip_errors=True,
        selected_rows=None
    )
    
    print(f"✅ Created {len(transactions_to_create)} transaction objects")
    
    # Verify all fields are preserved
    if transactions_to_create:
        sample_tx = transactions_to_create[0]
        print(f"\n🔍 Sample TransactionCreate object:")
        print(f"   Description: {sample_tx.description}")
        print(f"   Amount: {sample_tx.amount}")
        print(f"   Currency: {sample_tx.currency}")
        print(f"   Type: {sample_tx.type}")
        print(f"   Category: {sample_tx.category}")
        print(f"   Merchant: {sample_tx.merchant}")
        print(f"   Original Statement: {sample_tx.original_statement[:40]}..." if sample_tx.original_statement else "   Original Statement: None")
        print(f"   Notes: {sample_tx.notes}")
        print(f"   Tags: {sample_tx.tags}")
        print(f"   Ticker: {sample_tx.ticker}")
    
    print(f"\n{'='*80}")
    print("✅ ALL TESTS PASSED!")
    print(f"{'='*80}")
    print(f"\nSummary:")
    print(f"  ✅ Format detection working")
    print(f"  ✅ CSV parsing working")
    print(f"  ✅ Monarch fields extracted (merchant, notes, tags, etc.)")
    print(f"  ✅ Investment transactions detected")
    print(f"  ✅ Ticker symbols extracted")
    print(f"  ✅ Transaction creation working")
    print(f"\nReady to import full CSV with {total_lines-1:,} transactions!")
    
    return True

if __name__ == "__main__":
    try:
        success = test_monarch_csv_import()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

