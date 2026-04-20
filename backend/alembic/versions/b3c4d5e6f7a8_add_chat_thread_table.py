"""add_chat_thread_table

Revision ID: b3c4d5e6f7a8
Revises: a1b2c3d4e5f6
Create Date: 2026-04-20 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'chat_thread',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('paper_id', sa.String(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'messages',
            postgresql.JSONB(),
            nullable=False,
            server_default='[]',
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_chat_thread_paper_id', 'chat_thread', ['paper_id'])
    op.create_index('ix_chat_thread_user_id', 'chat_thread', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_chat_thread_user_id', table_name='chat_thread')
    op.drop_index('ix_chat_thread_paper_id', table_name='chat_thread')
    op.drop_table('chat_thread')
