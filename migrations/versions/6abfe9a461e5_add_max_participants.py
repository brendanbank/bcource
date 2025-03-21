"""add max participants

Revision ID: 6abfe9a461e5
Revises: fedda0f9c68a
Create Date: 2025-03-17 20:30:52.095931

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6abfe9a461e5'
down_revision = 'fedda0f9c68a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('training', schema=None) as batch_op:
        batch_op.add_column(sa.Column('max_participants', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('training', schema=None) as batch_op:
        batch_op.drop_column('max_participants')

    # ### end Alembic commands ###
