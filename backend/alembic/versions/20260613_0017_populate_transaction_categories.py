"""Map existing transactions to categories

Revision ID: 20260613_0017
Revises: 20260613_0016
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa

revision = "20260613_0017"
down_revision = "20260613_0016"


def upgrade():
    # Create mapping of transaction category strings to formal Category records
    # Match by category name or monarch_name
    op.execute("""
    UPDATE transactions
    SET category_id = (
        SELECT id FROM categories
        WHERE
            LOWER(categories.name) = LOWER(transactions.category)
            OR LOWER(categories.monarch_name) = LOWER(transactions.category)
        LIMIT 1
    )
    WHERE transactions.category IS NOT NULL
        AND transactions.category NOT IN ('', 'Uncategorized', 'Transfer', 'Income')
        AND category_id IS NULL;
    """)

    # For any remaining unmapped categories, create a fallback mapping to parent categories
    # Map common Monarch categories to our hierarchy
    op.execute("""
    UPDATE transactions
    SET category_id = (
        SELECT id FROM categories
        WHERE name IN ('Expenses', 'Income', 'Transfers', 'Investments', 'Debt')
            AND parent_category_id IS NULL
        ORDER BY CASE
            WHEN transactions.type = 'income' AND name = 'Income' THEN 1
            WHEN transactions.type = 'transfer' AND name = 'Transfers' THEN 1
            WHEN transactions.type IN ('buy', 'sell') AND name = 'Investments' THEN 1
            WHEN transactions.type = 'expense' AND name = 'Expenses' THEN 1
            ELSE 2
        END ASC
        LIMIT 1
    )
    WHERE category_id IS NULL
        AND transactions.category IS NOT NULL;
    """)


def downgrade():
    # Clear the category_id mapping (data is preserved in category column)
    op.execute("UPDATE transactions SET category_id = NULL;")
