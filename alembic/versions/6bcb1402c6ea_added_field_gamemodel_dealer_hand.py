"""added field GameModel.dealer_hand

Revision ID: 6bcb1402c6ea
Revises: 9b559eb86b5e
Create Date: 2023-03-10 13:29:27.127745

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6bcb1402c6ea'
down_revision = '9b559eb86b5e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('dealer_hand', sa.JSON(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('game', 'dealer_hand')
    # ### end Alembic commands ###
