"""Restructure strategy schema: merge backtest metrics into strategies, drop backtest_results

Revision ID: 002
Revises: 001
Create Date: 2026-04-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add backtest/evaluation columns to strategies ---
    op.add_column("strategies", sa.Column("hypothesis", sa.Text(), nullable=True))
    op.add_column("strategies", sa.Column("sharpe_ratio", sa.Float(), nullable=True))
    op.add_column("strategies", sa.Column("total_return_pct", sa.Float(), nullable=True))
    op.add_column("strategies", sa.Column("max_drawdown_pct", sa.Float(), nullable=True))
    op.add_column("strategies", sa.Column("win_rate_pct", sa.Float(), nullable=True))
    op.add_column("strategies", sa.Column("num_trades", sa.Integer(), nullable=True))
    op.add_column("strategies", sa.Column("backtest_start", sa.Date(), nullable=True))
    op.add_column("strategies", sa.Column("backtest_end", sa.Date(), nullable=True))
    op.add_column("strategies", sa.Column("ai_evaluation", sa.Text(), nullable=True))
    op.add_column("strategies", sa.Column("ai_score", sa.Float(), nullable=True))
    op.add_column(
        "strategies",
        sa.Column("approved", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("strategies", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column(
        "strategies",
        sa.Column("raw_output", postgresql.JSONB(), nullable=True),
    )

    # --- Remove unused columns from strategies ---
    op.drop_column("strategies", "name")
    op.drop_column("strategies", "description")
    op.drop_column("strategies", "parameters")
    op.drop_column("strategies", "iterations")

    # --- Drop backtest_results table ---
    op.drop_index("ix_backtest_results_strategy_id", table_name="backtest_results")
    op.drop_table("backtest_results")


def downgrade() -> None:
    # Recreate backtest_results
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

    # Restore removed strategy columns
    op.add_column("strategies", sa.Column("name", sa.String(255), nullable=True))
    op.add_column("strategies", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "strategies",
        sa.Column("parameters", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "strategies",
        sa.Column("iterations", sa.Integer(), nullable=False, server_default="0"),
    )

    # Remove new columns from strategies
    op.drop_column("strategies", "raw_output")
    op.drop_column("strategies", "rejection_reason")
    op.drop_column("strategies", "approved")
    op.drop_column("strategies", "ai_score")
    op.drop_column("strategies", "ai_evaluation")
    op.drop_column("strategies", "backtest_end")
    op.drop_column("strategies", "backtest_start")
    op.drop_column("strategies", "num_trades")
    op.drop_column("strategies", "win_rate_pct")
    op.drop_column("strategies", "max_drawdown_pct")
    op.drop_column("strategies", "total_return_pct")
    op.drop_column("strategies", "sharpe_ratio")
    op.drop_column("strategies", "hypothesis")
