"""Add category taxonomy model

Revision ID: 20260616_0015
Revises: 20260615_0014
Create Date: 2026-06-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '20260616_0015'
down_revision = '20260615_0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create categories table and seed with standard PFM categories."""

    # Create categories table
    op.create_table('categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=uuid.uuid4),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('icon', sa.String(length=10), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('name')
    )

    # Create indexes
    op.create_index('ix_categories_name', 'categories', ['name'])
    op.create_index('ix_categories_parent_id', 'categories', ['parent_id'])
    op.create_index('ix_categories_is_active', 'categories', ['is_active'])

    # Seed standard categories
    op.execute("""
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system) VALUES
        -- Top-level: Income
        (gen_random_uuid(), 'income', 'Income', '💰', 'green', NULL, true),
        -- Top-level: Expenses
        (gen_random_uuid(), 'food_dining', 'Food & Dining', '🍽️', 'orange', NULL, true),
        (gen_random_uuid(), 'transportation', 'Transportation', '🚗', 'blue', NULL, true),
        (gen_random_uuid(), 'bills_utilities', 'Bills & Utilities', '💡', 'yellow', NULL, true),
        (gen_random_uuid(), 'shopping', 'Shopping', '🛍️', 'purple', NULL, true),
        (gen_random_uuid(), 'entertainment', 'Entertainment', '🎭', 'pink', NULL, true),
        (gen_random_uuid(), 'healthcare', 'Healthcare', '🏥', 'red', NULL, true),
        (gen_random_uuid(), 'housing', 'Housing', '🏠', 'indigo', NULL, true),
        (gen_random_uuid(), 'travel', 'Travel', '✈️', 'sky', NULL, true),
        (gen_random_uuid(), 'personal_care', 'Personal Care', '💇', 'rose', NULL, true),
        (gen_random_uuid(), 'education', 'Education', '📚', 'cyan', NULL, true),
        (gen_random_uuid(), 'gifts_donations', 'Gifts & Donations', '🎁', 'emerald', NULL, true),
        (gen_random_uuid(), 'fees_charges', 'Fees & Charges', '💸', 'gray', NULL, true),
        (gen_random_uuid(), 'other', 'Other', '📌', 'slate', NULL, true);
    """)

    # Add child categories
    op.execute("""
        -- Income children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'salary', 'Salary', '💰', 'green', id, true
        FROM categories WHERE name = 'income';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'investment_income', 'Investment Income', '📈', 'green', id, true
        FROM categories WHERE name = 'income';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'business_income', 'Business Income', '💼', 'green', id, true
        FROM categories WHERE name = 'income';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'other_income', 'Other Income', '💰', 'green', id, true
        FROM categories WHERE name = 'income';

        -- Food & Dining children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'groceries', 'Groceries', '🛒', 'orange', id, true
        FROM categories WHERE name = 'food_dining';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'restaurants', 'Restaurants', '🍽️', 'orange', id, true
        FROM categories WHERE name = 'food_dining';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'coffee_shops', 'Coffee Shops', '☕', 'orange', id, true
        FROM categories WHERE name = 'food_dining';

        -- Transportation children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'gas_fuel', 'Gas & Fuel', '⛽', 'blue', id, true
        FROM categories WHERE name = 'transportation';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'parking', 'Parking', '🅿️', 'blue', id, true
        FROM categories WHERE name = 'transportation';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'public_transit', 'Public Transit', '🚌', 'blue', id, true
        FROM categories WHERE name = 'transportation';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'auto_insurance', 'Auto Insurance', '🚗', 'blue', id, true
        FROM categories WHERE name = 'transportation';

        -- Bills & Utilities children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'electricity', 'Electricity', '💡', 'yellow', id, true
        FROM categories WHERE name = 'bills_utilities';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'water', 'Water', '💧', 'yellow', id, true
        FROM categories WHERE name = 'bills_utilities';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'internet', 'Internet', '🌐', 'yellow', id, true
        FROM categories WHERE name = 'bills_utilities';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'phone', 'Phone', '📱', 'yellow', id, true
        FROM categories WHERE name = 'bills_utilities';

        -- Shopping children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'clothing', 'Clothing', '👔', 'purple', id, true
        FROM categories WHERE name = 'shopping';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'electronics', 'Electronics', '💻', 'purple', id, true
        FROM categories WHERE name = 'shopping';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'home_goods', 'Home Goods', '🏠', 'purple', id, true
        FROM categories WHERE name = 'shopping';

        -- Entertainment children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'movies', 'Movies', '🎬', 'pink', id, true
        FROM categories WHERE name = 'entertainment';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'music', 'Music', '🎵', 'pink', id, true
        FROM categories WHERE name = 'entertainment';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'sports', 'Sports', '⚽', 'pink', id, true
        FROM categories WHERE name = 'entertainment';

        -- Housing children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'rent', 'Rent', '🏠', 'indigo', id, true
        FROM categories WHERE name = 'housing';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'mortgage', 'Mortgage', '🏘️', 'indigo', id, true
        FROM categories WHERE name = 'housing';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'home_improvement', 'Home Improvement', '🔧', 'indigo', id, true
        FROM categories WHERE name = 'housing';

        -- Healthcare children
        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'doctor', 'Doctor', '🏥', 'red', id, true
        FROM categories WHERE name = 'healthcare';

        INSERT INTO categories (id, name, display_name, icon, color, parent_id, is_system)
        SELECT gen_random_uuid(), 'pharmacy', 'Pharmacy', '💊', 'red', id, true
        FROM categories WHERE name = 'healthcare';
    """)


def downgrade() -> None:
    """Drop categories table."""
    op.drop_index('ix_categories_is_active', table_name='categories')
    op.drop_index('ix_categories_parent_id', table_name='categories')
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_table('categories')
