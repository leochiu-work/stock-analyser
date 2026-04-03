"""Initial tables: tickers and news

Revision ID: 001
Revises:
Create Date: 2026-04-03
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
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("last_fetch_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="uq_ticker_symbol"),
    )

    op.create_table(
        "news",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_symbol", sa.String(length=20), nullable=False),
        sa.Column("finnhub_id", sa.BigInteger(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("image", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("finnhub_id", name="uq_news_finnhub_id"),
    )
    op.create_index("ix_news_ticker_symbol", "news", ["ticker_symbol"])
    op.create_index("ix_news_published_at", "news", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_news_published_at", table_name="news")
    op.drop_index("ix_news_ticker_symbol", table_name="news")
    op.drop_table("news")
    op.drop_table("tickers")
