"""Add category taxonomy table with hierarchy support

Revision ID: 20260613_0016
Revises: 20260613_0015
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260613_0016"
down_revision = "20260613_0015"


def upgrade():
    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("parent_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("monarch_name", sa.String(100), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_category_id"], ["categories.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_categories_name", "categories", ["name"])
    op.create_index("ix_categories_monarch_name", "categories", ["monarch_name"])
    op.create_index("ix_categories_parent_id", "categories", ["parent_category_id"])
    op.create_index("ix_categories_created_at", "categories", ["created_at"])

    # Add category_id FK to transactions table
    op.add_column(
        "transactions",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])

    # Seed default categories
    # Using raw SQL since Alembic op doesn't have a direct way to insert data with UUID generation
    op.execute("""
    INSERT INTO categories (id, name, description, monarch_name, icon, created_at, updated_at) VALUES
    (gen_random_uuid(), 'Income', 'Income and earnings', 'Income', 'trending-up', NOW(), NOW()),
    (gen_random_uuid(), 'Expenses', 'General expenses', NULL, 'trending-down', NOW(), NOW()),
    (gen_random_uuid(), 'Transfers', 'Transfers between accounts', 'Transfer', 'arrow-right-left', NOW(), NOW()),
    (gen_random_uuid(), 'Investments', 'Investment transactions', 'Investments', 'briefcase', NOW(), NOW()),
    (gen_random_uuid(), 'Debt', 'Debt payments and interest', NULL, 'credit-card', NOW(), NOW());
    """)

    # Seed subcategories under Expenses
    op.execute("""
    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Groceries', 'Grocery shopping', id, 'Groceries', 'shopping-cart', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Dining Out', 'Restaurants and cafes', id, 'Restaurants', 'utensils', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Utilities', 'Electric, gas, water, internet', id, 'Utilities', 'zap', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Transportation', 'Gas, transit, parking', id, 'Transportation', 'car', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Shopping', 'Retail and merchandise', id, 'Shopping', 'shopping-bag', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Entertainment', 'Movies, games, hobbies', id, 'Entertainment', 'film', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Healthcare', 'Medical and pharmacy', id, 'Healthcare', 'heart', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;

    INSERT INTO categories (id, name, description, parent_category_id, monarch_name, icon, created_at, updated_at)
    SELECT gen_random_uuid(), 'Fees', 'Bank fees and charges', id, 'Fees', 'percent', NOW(), NOW()
    FROM categories WHERE name = 'Expenses' LIMIT 1;
    """)


def downgrade():
    # Drop indexes and foreign key
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "category_id")

    # Drop categories table and indexes
    op.drop_index("ix_categories_created_at", table_name="categories")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_index("ix_categories_monarch_name", table_name="categories")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_table("categories")
