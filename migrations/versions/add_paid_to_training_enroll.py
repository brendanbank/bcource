"""Add paid field to TrainingEnroll

Revision ID: add_paid_field
Revises: sms_2fa_phone
Create Date: 2026-02-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_paid_field'
down_revision = 'sms_2fa_phone'
branch_labels = None
depends_on = None


def upgrade():
    """Add paid column to training_enroll table."""
    op.add_column('training_enroll', sa.Column('paid', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    """Remove paid column from training_enroll table."""
    op.drop_column('training_enroll', 'paid')
