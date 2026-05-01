"""Add assistant conversations table

Revision ID: 20260501_0013
Revises: 20260424_0012
Create Date: 2026-05-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260501_0013"
down_revision = "20260424_0012"


def upgrade():
    op.create_table(
        "assistant_conversations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("assistant_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),  # 'user' or 'assistant'
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("functions_called", postgresql.JSONB(), nullable=True),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index("ix_assistant_messages_conversation_id", "assistant_messages", ["conversation_id"])
    op.create_index("ix_assistant_messages_created_at", "assistant_messages", ["created_at"])


def downgrade():
    op.drop_index("ix_assistant_messages_created_at")
    op.drop_index("ix_assistant_messages_conversation_id")
    op.drop_table("assistant_messages")
    op.drop_table("assistant_conversations")
