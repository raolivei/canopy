# CSV Import Guide

Canopy provides comprehensive CSV import functionality to help you import transactions from various financial institutions and apps like Monarch Money, Chase, Bank of America, and more.

## Quick Start

1. Navigate to the **Import** page from the sidebar
2. Select your bank format from the dropdown (or use Generic for custom CSVs)
3. Drag and drop your CSV file or click to browse
4. Review the import preview
5. Click "Import" to add transactions to your account

## Supported Formats

### Monarch Money
Full support for Monarch Money CSV exports including:
- Clean merchant names
- Original statement text
- Categories and tags
- Investment transactions (Buy/Sell)
- Multiple account tracking
- Notes

**Required Columns:** Date, Merchant, Category, Account, Amount

### Chase Bank
- **Columns:** Posting Date, Description, Amount, Type, Category, Balance
- **Date Format:** MM/DD/YYYY

### Bank of America
- **Columns:** Date, Description, Amount, Running Bal.
- **Date Format:** MM/DD/YYYY

### Wells Fargo
- **Columns:** Date, Description, Amount
- **Date Format:** MM/DD/YYYY

### Capital One
- **Columns:** Transaction Date, Description, Debit, Credit, Category
- **Date Format:** YYYY-MM-DD

### American Express
- **Columns:** Date, Description, Amount
- **Date Format:** MM/DD/YYYY

### TD Bank
- **Columns:** Date, Description, Debit, Credit
- **Date Format:** MM/DD/YYYY

### RBC (Royal Bank of Canada)
- **Columns:** Transaction Date, Description, Debit, Credit, Account Number
- **Date Format:** MM/DD/YYYY

### Nubank
- **Columns:** date, title, amount, category
- **Date Format:** YYYY-MM-DD

### Generic CSV
Use this option for any CSV file and manually map columns using the custom mapping feature.

## Features

### 🎯 Smart Format Detection
Canopy automatically detects your bank's CSV format based on column headers.

### 🔍 Duplicate Detection
The system checks for duplicate transactions based on:
- Transaction date
- Amount
- Description

Duplicates are flagged in the preview and can be skipped during import.

### 💰 Multi-Currency Support
Import transactions in any of these currencies:
- USD (US Dollar)
- CAD (Canadian Dollar)
- BRL (Brazilian Real)
- EUR (Euro)
- GBP (British Pound)

### 📊 Import Preview
Before importing, you'll see:
- Total rows detected
- Valid transactions
- Number of duplicates
- Any errors or issues
- Transaction details preview

### 🏷️ Rich Transaction Data
When importing from Monarch Money or using custom mapping, you get:
- **Merchant** - Clean merchant name (e.g., "Apple", "Starbucks")
- **Original Statement** - Raw bank statement text
- **Category** - Transaction category
- **Account** - Source account
- **Notes** - Transaction notes
- **Tags** - Transaction tags
- **Ticker** - Stock ticker for investment transactions

### 📈 Investment Tracking
Import investment transactions with automatic detection of:
- Buy/Sell transactions
- Ticker symbols (e.g., VTI, AAPL, ZJPN.F)
- Transaction amounts

## Custom Field Mapping

If your bank's CSV format isn't in the presets, you can use custom mapping:

1. Select "Custom" from the Bank Format dropdown
2. Upload your CSV
3. Map the columns:
   - **Date Column** (required)
   - **Description Column** (required)
   - **Amount Column** OR **Debit/Credit Columns** (required)
   - Category Column (optional)
   - Account Column (optional)
   - Merchant Column (optional)
   - Notes Column (optional)
   - Tags Column (optional)

### Example CSV Formats

See the `examples/` directory for sample CSV files:
- `monarch_transactions.csv` - Full Monarch Money export
- `chase_transactions.csv` - Chase Bank format
- `generic_transactions.csv` - Simple generic format

## CSV Format Requirements

### Minimum Requirements
Your CSV must have at least:
1. A date column
2. A description column
3. An amount column (or separate debit/credit columns)

### Date Formats
Supported date formats include:
- YYYY-MM-DD (2025-01-15)
- MM/DD/YYYY (01/15/2025)
- DD/MM/YYYY (15/01/2025)
- YYYY/MM/DD (2025/01/15)

### Amount Formats
Supported amount formats:
- Decimal: `123.45`
- With currency symbol: `$123.45`, `€123.45`, `R$123.45`
- With commas: `1,234.56`
- Negative: `-123.45`
- Accounting format: `(123.45)` = negative

### Transaction Types
The system automatically infers transaction types:
- **Income** - Positive amounts, deposits, payments received
- **Expense** - Negative amounts, purchases, withdrawals
- **Transfer** - Account transfers
- **Buy** - Investment purchases
- **Sell** - Investment sales

## Import History

View your import history to track:
- Import date and time
- File name
- Number of transactions imported
- Number skipped (duplicates)
- Any errors encountered

## Troubleshooting

### "Failed to parse date"
- Check that your CSV uses one of the supported date formats
- Try manually specifying the date format in custom mapping

### "No transactions detected"
- Verify your CSV has data rows (not just headers)
- Check that columns are properly separated by commas
- Try opening the CSV in a text editor to verify format

### "Duplicate transactions"
- This means transactions with the same date, amount, and description already exist
- You can choose to skip duplicates (recommended) or import them anyway

### "Failed to detect bank format"
- Use the "Generic" or "Custom" format option
- Manually map your CSV columns

## API Reference

### Preview Import
```bash
curl -X POST http://localhost:8000/v1/csv-import/preview \
  -F "file=@transactions.csv" \
  -F "bank_format=monarch" \
  -F "default_currency=USD"
```

### Import Transactions
```bash
curl -X POST http://localhost:8000/v1/csv-import/import \
  -H "Content-Type: application/json" \
  -d '{
    "import_id": "uuid-here",
    "skip_duplicates": true,
    "skip_errors": true
  }'
```

### Get Import History
```bash
curl http://localhost:8000/v1/csv-import/history
```

## Best Practices

1. **Always preview before importing** - Check for errors and duplicates
2. **Keep original CSV files** - Store backups of your bank exports
3. **Import regularly** - Weekly or monthly imports are easier to manage
4. **Review categories** - Monarch Money has excellent categorization; other banks may need manual category assignment
5. **Use tags** - Tag transactions for better organization
6. **Check for duplicates** - Enable duplicate detection to avoid double-counting

## Tips for Monarch Money Users

Monarch Money exports contain rich data. To get the most out of it:
- Export from Monarch regularly to keep LedgerLight in sync
- The "Original Statement" field preserves raw bank data for reference
- Investment transactions automatically extract ticker symbols
- Categories are preserved exactly as in Monarch
- Use the Account field to track which credit card or bank account was used

## Support

For additional help or to report issues with CSV imports:
- Check the main README.md
- Review ARCHITECTURE.md for technical details
- Open an issue on GitHub

