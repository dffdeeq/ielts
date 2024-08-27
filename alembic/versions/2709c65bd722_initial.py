"""initial

Revision ID: 2709c65bd722
Revises: 
Create Date: 2024-06-19 21:09:18.534153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2709c65bd722'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('question',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('competence', sa.Enum('writing', 'speaking', 'listening', 'reading', name='competenceenum'), nullable=True),
    sa.Column('question_json', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('date_modified', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tg_user',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tg_user_question',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Boolean(), nullable=True),
    sa.Column('start_timestamp', sa.DateTime(), nullable=True),
    sa.Column('send_feedback_timestamp', sa.DateTime(), nullable=True),
    sa.Column('is_liked', sa.Boolean(), nullable=True),
    sa.Column('user_answer_json', sa.JSON(), nullable=True),
    sa.Column('user_result_json', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['question.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['tg_user.id'], ),
    sa.PrimaryKeyConstraint('id', 'user_id', 'question_id'),
    sa.UniqueConstraint('user_id', 'question_id', name='uq_user_question')
    )
    op.create_index('uq_tg_user_question_id', 'tg_user_question', ['id'], unique=True)
    op.create_table('temp_data',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('tg_user_question_id', sa.Integer(), nullable=False),
    sa.Column('part', sa.Enum('first', 'second', 'third', name='partenum'), nullable=True),
    sa.Column('question_text', sa.String(), nullable=True),
    sa.Column('filename', sa.String(), nullable=True),
    sa.Column('answer_text', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['tg_user_question_id'], ['tg_user_question.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('temp_data')
    op.drop_index('uq_tg_user_question_id', table_name='tg_user_question')
    op.drop_table('tg_user_question')
    op.drop_table('tg_user')
    op.drop_table('question')
    # ### end Alembic commands ###
