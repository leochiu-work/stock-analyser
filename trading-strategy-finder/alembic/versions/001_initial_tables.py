"""Initial tables: strategies and backtest_results

Revision ID: 001
Revises:
Create Date: 2026-04-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=True),
        sa.Column("iterations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategies_ticker", "strategies", ["ticker"])
    op.create_index("ix_strategies_status", "strategies", ["status"])

    op.create_table(
        "backtest_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "strategy_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("strategies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("total_return_pct", sa.Float(), nullable=True),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=True),
        sa.Column("win_rate_pct", sa.Float(), nullable=True),
        sa.Column("num_trades", sa.Integer(), nullable=True),
        sa.Column("backtest_start", sa.Date(), nullable=True),
        sa.Column("backtest_end", sa.Date(), nullable=True),
        sa.Column("ai_evaluation", sa.Text(), nullable=True),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("raw_output", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_backtest_results_strategy_id", "backtest_results", ["strategy_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_backtest_results_strategy_id", table_name="backtest_results")
    op.drop_table("backtest_results")
    op.drop_index("ix_strategies_status", table_name="strategies")
    op.drop_index("ix_strategies_ticker", table_name="strategies")
    op.drop_table("strategies")
