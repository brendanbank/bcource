"""Add OneTimePassword model for OTP authentication

Revision ID: otp_authentication
Revises: 841e8462a7aa
Create Date: 2025-10-08 16:53:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'otp_authentication'
down_revision = '841e8462a7aa'
branch_labels = None
depends_on = None


def upgrade():
    """Create the one_time_password table."""
    op.create_table(
        'one_time_password',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=256), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('request_ip', sa.String(length=45), nullable=True),
        sa.Column('purpose', sa.String(length=64), nullable=False, default='login'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for common queries
    op.create_index('ix_otp_user_id', 'one_time_password', ['user_id'])
    op.create_index('ix_otp_used', 'one_time_password', ['used'])
    op.create_index('ix_otp_expires_at', 'one_time_password', ['expires_at'])
    op.create_index('ix_otp_purpose', 'one_time_password', ['purpose'])


def downgrade():
    """Drop the one_time_password table."""
    op.drop_index('ix_otp_purpose', table_name='one_time_password')
    op.drop_index('ix_otp_expires_at', table_name='one_time_password')
    op.drop_index('ix_otp_used', table_name='one_time_password')
    op.drop_index('ix_otp_user_id', table_name='one_time_password')
    op.drop_table('one_time_password')
