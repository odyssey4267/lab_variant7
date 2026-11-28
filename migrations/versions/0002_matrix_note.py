"""Добавить в таблицу matrix необязательное поле note (примечание).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("matrix") as batch:
        batch.add_column(sa.Column("note", sa.String(200), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("matrix") as batch:
        batch.drop_column("note")
