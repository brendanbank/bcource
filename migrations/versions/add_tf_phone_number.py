"""Add tf_phone_number field for SMS 2FA

Revision ID: sms_2fa_phone
Revises: otp_authentication
Create Date: 2025-10-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'sms_2fa_phone'
down_revision = 'otp_authentication'
branch_labels = None
depends_on = None


def upgrade():
    """Add tf_phone_number column to user table."""
    op.add_column('user', sa.Column('tf_phone_number', sa.String(length=32), nullable=True))


def downgrade():
    """Remove tf_phone_number column from user table."""
    op.drop_column('user', 'tf_phone_number')
