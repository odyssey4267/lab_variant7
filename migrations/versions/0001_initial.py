"""Начальная схема: матрицы, ячейки, теги, анализы, результаты, настройки.

Revision ID: 0001
Revises:
Create Date: 2026-11-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matrix",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("n_rows", sa.Integer(), nullable=False),
        sa.Column("n_cols", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(),
                  nullable=False),
        sa.CheckConstraint("n_rows >= 1", name="ck_matrix_rows"),
        sa.CheckConstraint("n_cols >= 1", name="ck_matrix_cols"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "tag",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "matrix_cell",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("matrix_id", sa.Integer(), sa.ForeignKey("matrix.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("row_idx", sa.Integer(), nullable=False),
        sa.Column("col_idx", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.UniqueConstraint("matrix_id", "row_idx", "col_idx", name="uq_cell_pos"),
    )
    op.create_index("ix_matrix_cell_matrix_id", "matrix_cell", ["matrix_id"])
    op.create_table(
        "matrix_tag",
        sa.Column("matrix_id", sa.Integer(), sa.ForeignKey("matrix.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tag.id", ondelete="CASCADE"),
                  primary_key=True),
    )
    op.create_table(
        "analysis",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("matrix_id", sa.Integer(), sa.ForeignKey("matrix.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("eps", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(),
                  nullable=False),
    )
    op.create_index("ix_analysis_matrix_id", "analysis", ["matrix_id"])
    op.create_table(
        "vector_result",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("value", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('zero_columns', 'descending_rows', 'symmetric_rows')", name="ck_result_kind"),
        sa.UniqueConstraint("analysis_id", "kind", "position", name="uq_result_pos"),
    )
    op.create_index("ix_vector_result_analysis_id", "vector_result", ["analysis_id"])
    op.create_table(
        "setting",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("value", sa.String(200), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("setting")
    op.drop_index("ix_vector_result_analysis_id", table_name="vector_result")
    op.drop_table("vector_result")
    op.drop_index("ix_analysis_matrix_id", table_name="analysis")
    op.drop_table("analysis")
    op.drop_table("matrix_tag")
    op.drop_index("ix_matrix_cell_matrix_id", table_name="matrix_cell")
    op.drop_table("matrix_cell")
    op.drop_table("tag")
    op.drop_table("matrix")
