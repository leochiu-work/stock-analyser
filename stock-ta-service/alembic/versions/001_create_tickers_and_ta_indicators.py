"""create tickers and ta_indicators tables

Revision ID: 001
Revises:
Create Date: 2026-04-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("symbol", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="uq_ticker_symbol"),
    )

    op.create_table(
        "ta_indicators",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("sma_20", sa.Float(), nullable=True),
        sa.Column("sma_50", sa.Float(), nullable=True),
        sa.Column("sma_200", sa.Float(), nullable=True),
        sa.Column("ema_12", sa.Float(), nullable=True),
        sa.Column("ema_26", sa.Float(), nullable=True),
        sa.Column("rsi_14", sa.Float(), nullable=True),
        sa.Column("macd_line", sa.Float(), nullable=True),
        sa.Column("macd_signal", sa.Float(), nullable=True),
        sa.Column("macd_hist", sa.Float(), nullable=True),
        sa.Column("bb_upper", sa.Float(), nullable=True),
        sa.Column("bb_middle", sa.Float(), nullable=True),
        sa.Column("bb_lower", sa.Float(), nullable=True),
        sa.Column("atr_14", sa.Float(), nullable=True),
        sa.Column("stoch_k", sa.Float(), nullable=True),
        sa.Column("stoch_d", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "date", name="uq_ta_ticker_date"),
    )
    op.create_index("ix_ta_ticker_date", "ta_indicators", ["ticker", "date"])


def downgrade() -> None:
    op.drop_index("ix_ta_ticker_date", table_name="ta_indicators")
    op.drop_table("ta_indicators")
    op.drop_table("tickers")
