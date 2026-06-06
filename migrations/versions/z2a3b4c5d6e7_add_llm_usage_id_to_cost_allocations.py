"""add llm_usage_id to cost_allocations

Revision ID: z2a3b4c5d6e7
Revises: e032c87d2d9c
Create Date: 2026-06-03 21:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "z2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e032c87d2d9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make cost_record_id nullable
    op.alter_column(
        "cost_allocations", "cost_record_id", existing_type=sa.Uuid(), nullable=True
    )
    # Add llm_usage_id column
    op.add_column(
        "cost_allocations", sa.Column("llm_usage_id", sa.Uuid(), nullable=True)
    )
    # Add index on llm_usage_id
    op.create_index(
        "ix_cost_allocations_llm_usage",
        "cost_allocations",
        ["llm_usage_id"],
        unique=False,
    )
    # Add check constraint
    op.create_check_constraint(
        "chk_cost_allocations_target_type",
        "cost_allocations",
        "(cost_record_id IS NOT NULL AND llm_usage_id IS NULL) OR (cost_record_id IS NULL AND llm_usage_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_cost_allocations_target_type", "cost_allocations", type_="check"
    )
    op.drop_index("ix_cost_allocations_llm_usage", table_name="cost_allocations")
    op.drop_column("cost_allocations", "llm_usage_id")
    op.alter_column(
        "cost_allocations", "cost_record_id", existing_type=sa.Uuid(), nullable=False
    )
