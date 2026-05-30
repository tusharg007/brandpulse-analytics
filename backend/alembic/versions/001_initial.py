"""Initial migration — create brands, sales_records, etl_logs tables.

Revision ID: 001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Brands table ────────────────────────────────────
    op.create_table(
        'brands',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('launch_date', sa.Date(), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
    )

    # ── Sales records table ─────────────────────────────
    op.create_table(
        'sales_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('revenue', sa.Float(), nullable=False),
        sa.Column('units_sold', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('return_rate', sa.Float(), default=0.0),
        sa.Column('revenue_per_unit', sa.Float()),
        sa.Column('is_anomalous', sa.Boolean(), default=False),
        sa.Column('ingestion_timestamp', sa.DateTime()),
        sa.UniqueConstraint('brand_id', 'date', 'platform', name='uq_brand_date_platform'),
    )

    # ── ETL logs table ──────────────────────────────────
    op.create_table(
        'etl_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('run_timestamp', sa.DateTime(), nullable=False),
        sa.Column('records_processed', sa.Integer(), default=0),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('etl_logs')
    op.drop_table('sales_records')
    op.drop_table('brands')
