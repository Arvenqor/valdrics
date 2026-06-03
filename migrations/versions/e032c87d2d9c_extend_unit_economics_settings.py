"""extend_unit_economics_settings

Revision ID: e032c87d2d9c
Revises: y1z2a3b4c5d6
Create Date: 2026-05-31 07:11:41.828987

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e032c87d2d9c'
down_revision: Union[str, Sequence[str], None] = 'y1z2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Extend unit_economics_settings with target KPI columns.

    Three-step migration so existing rows get sensible values before the
    NOT NULL constraint is applied:

    1. Add columns as nullable.
    2. Back-fill existing rows with domain defaults.
    3. Alter columns to NOT NULL.
    """
    # 1. Add columns as nullable first
    op.add_column(
        'unit_economics_settings',
        sa.Column('target_spend_reduction_pct', sa.Numeric(precision=8, scale=2), nullable=True),
    )
    op.add_column(
        'unit_economics_settings',
        sa.Column('target_rollout_days', sa.Integer(), nullable=True),
    )
    op.add_column(
        'unit_economics_settings',
        sa.Column('target_team_members', sa.Integer(), nullable=True),
    )
    op.add_column(
        'unit_economics_settings',
        sa.Column('target_blended_hourly_rate', sa.Numeric(precision=8, scale=2), nullable=True),
    )

    # 2. Back-fill existing rows with domain defaults
    op.execute(
        """
        UPDATE unit_economics_settings
        SET
            target_spend_reduction_pct  = 15.0,
            target_rollout_days         = 30,
            target_team_members         = 10,
            target_blended_hourly_rate  = 75.0
        WHERE
            target_spend_reduction_pct IS NULL
        """
    )

    # 3. Enforce NOT NULL constraint now that all rows have values
    op.alter_column(
        'unit_economics_settings',
        'target_spend_reduction_pct',
        nullable=False,
    )
    op.alter_column(
        'unit_economics_settings',
        'target_rollout_days',
        nullable=False,
    )
    op.alter_column(
        'unit_economics_settings',
        'target_team_members',
        nullable=False,
    )
    op.alter_column(
        'unit_economics_settings',
        'target_blended_hourly_rate',
        nullable=False,
    )


def downgrade() -> None:
    """Drop target KPI columns from unit_economics_settings."""
    op.drop_column('unit_economics_settings', 'target_blended_hourly_rate')
    op.drop_column('unit_economics_settings', 'target_team_members')
    op.drop_column('unit_economics_settings', 'target_rollout_days')
    op.drop_column('unit_economics_settings', 'target_spend_reduction_pct')
