"""002 — Add chat tables and ETL log columns.

Revision ID: 002_chat_and_etl
Revises: 001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = '002_chat_and_etl'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Chat rooms table
    op.create_table(
        'chat_rooms',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('brand_id', sa.Integer(), sa.ForeignKey('brands.id'), nullable=True),
        sa.Column('room_type', sa.String(20)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('room_id', sa.Integer(), sa.ForeignKey('chat_rooms.id'), nullable=False),
        sa.Column('sender_name', sa.String(100)),
        sa.Column('sender_type', sa.String(20)),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), server_default='text'),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
    )

    # Add new columns to etl_logs
    op.add_column('etl_logs', sa.Column('anomalies_detected', sa.Integer(), server_default='0'))
    op.add_column('etl_logs', sa.Column('duration_seconds', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('etl_logs', 'duration_seconds')
    op.drop_column('etl_logs', 'anomalies_detected')
    op.drop_table('chat_messages')
    op.drop_table('chat_rooms')
