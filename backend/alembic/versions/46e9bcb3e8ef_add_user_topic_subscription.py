"""add user topic subscription

Revision ID: 46e9bcb3e8ef
Revises: d9e2f1a3b4c5
Create Date: 2026-07-12 00:16:28.339587

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '46e9bcb3e8ef'
down_revision: Union[str, Sequence[str], None] = 'd9e2f1a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = 'user_topic_subscription'


def upgrade() -> None:
	"""Upgrade schema."""
	op.create_table(
		TABLE,
		sa.Column('id', sa.Uuid(), nullable=False),
		sa.Column('user_id', sa.UUID(), nullable=False),
		sa.Column('keywords', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
		sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
		sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
		sa.PrimaryKeyConstraint('id'),
	)
	op.create_index(op.f('ix_user_topic_subscription_user_id'), TABLE, ['user_id'], unique=True)

	# RLS: the backend uses the service role and bypasses these policies; they
	# guard direct client (Supabase JS) access so users only see their own row.
	op.enable_rls(TABLE)
	op.create_rls_policy(
		'topic_subscription_select',
		TABLE,
		command='SELECT',
		to='authenticated',
		using='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'topic_subscription_insert',
		TABLE,
		command='INSERT',
		to='authenticated',
		with_check='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'topic_subscription_update',
		TABLE,
		command='UPDATE',
		to='authenticated',
		using='auth.uid() = user_id',
		with_check='auth.uid() = user_id',
	)
	op.create_rls_policy(
		'topic_subscription_delete',
		TABLE,
		command='DELETE',
		to='authenticated',
		using='auth.uid() = user_id',
	)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_rls_policy('topic_subscription_delete', TABLE)
	op.drop_rls_policy('topic_subscription_update', TABLE)
	op.drop_rls_policy('topic_subscription_insert', TABLE)
	op.drop_rls_policy('topic_subscription_select', TABLE)
	op.disable_rls(TABLE)
	op.drop_index(op.f('ix_user_topic_subscription_user_id'), table_name=TABLE)
	op.drop_table(TABLE)
