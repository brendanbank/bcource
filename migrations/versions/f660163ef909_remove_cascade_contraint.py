"""remove cascade contraint

Revision ID: f660163ef909
Revises: 012592f43031
Create Date: 2025-03-18 08:27:08.524290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f660163ef909'
down_revision = '012592f43031'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('training_event', schema=None) as batch_op:
        batch_op.drop_constraint('training_event_ibfk_1', type_='foreignkey')
        batch_op.create_foreign_key(None, 'training', ['training_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('training_event', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('training_event_ibfk_1', 'training', ['training_id'], ['id'], ondelete='CASCADE')

    # ### end Alembic commands ###
