"""add digest delivery log

Revision ID: 78cc8be73d74
Revises: 46e9bcb3e8ef
Create Date: 2026-07-12 01:01:35.483457

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '78cc8be73d74'
down_revision: Union[str, Sequence[str], None] = '46e9bcb3e8ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE = 'digest_delivery_log'


def upgrade() -> None:
	"""Upgrade schema."""
	op.create_table(
		TABLE,
		sa.Column('id', sa.Uuid(), nullable=False),
		sa.Column('user_id', sa.UUID(), nullable=False),
		sa.Column('blog_post_id', sa.UUID(), nullable=False),
		sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
		sa.PrimaryKeyConstraint('id'),
		sa.UniqueConstraint('user_id', 'blog_post_id', name='uq_digest_delivery_user_blog'),
	)
	op.create_index(op.f('ix_digest_delivery_log_user_id'), TABLE, ['user_id'], unique=False)

	# RLS: rows are written by the backend (service role, bypasses RLS). The policy
	# only lets an authenticated user read their own delivery history.
	op.enable_rls(TABLE)
	op.create_rls_policy(
		'digest_delivery_select',
		TABLE,
		command='SELECT',
		to='authenticated',
		using='auth.uid() = user_id',
	)


def downgrade() -> None:
	"""Downgrade schema."""
	op.drop_rls_policy('digest_delivery_select', TABLE)
	op.disable_rls(TABLE)
	op.drop_index(op.f('ix_digest_delivery_log_user_id'), table_name=TABLE)
	op.drop_table(TABLE)
