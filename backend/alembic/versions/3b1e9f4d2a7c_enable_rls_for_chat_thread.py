"""enable_rls_for_chat_thread

Revision ID: 3b1e9f4d2a7c
Revises: f8754dbb89e2
Create Date: 2026-04-27 05:30:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3b1e9f4d2a7c'
down_revision: Union[str, Sequence[str], None] = 'f8754dbb89e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CHAT_THREAD_TABLE = 'chat_thread'


def upgrade() -> None:
	op.enable_rls(CHAT_THREAD_TABLE)

	op.create_rls_policy(
		'chat_thread_select',
		CHAT_THREAD_TABLE,
		command='SELECT',
		to='authenticated',
		using='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'chat_thread_insert',
		CHAT_THREAD_TABLE,
		command='INSERT',
		to='authenticated',
		with_check='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'chat_thread_update',
		CHAT_THREAD_TABLE,
		command='UPDATE',
		to='authenticated',
		using='auth.uid() = user_id',
		with_check='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'chat_thread_delete',
		CHAT_THREAD_TABLE,
		command='DELETE',
		to='authenticated',
		using='auth.uid() = user_id',
	)


def downgrade() -> None:
	op.drop_rls_policy('chat_thread_delete', CHAT_THREAD_TABLE)
	op.drop_rls_policy('chat_thread_update', CHAT_THREAD_TABLE)
	op.drop_rls_policy('chat_thread_insert', CHAT_THREAD_TABLE)
	op.drop_rls_policy('chat_thread_select', CHAT_THREAD_TABLE)

	op.disable_rls(CHAT_THREAD_TABLE)
