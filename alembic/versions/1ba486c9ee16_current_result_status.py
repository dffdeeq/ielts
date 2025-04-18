"""current_result_status

Revision ID: 1ba486c9ee16
Revises: ecaac7959be3
Create Date: 2024-07-18 20:23:37.495024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ba486c9ee16'
down_revision: Union[str, None] = 'ecaac7959be3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tg_user_question', sa.Column('current_result_status', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tg_user_question', 'current_result_status')
    # ### end Alembic commands ###
