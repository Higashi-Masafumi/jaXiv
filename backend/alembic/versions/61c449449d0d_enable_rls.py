"""enable_rls

Revision ID: 61c449449d0d
Revises: a1b2c3d4e5f6
Create Date: 2026-04-17 03:16:17.316477

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '61c449449d0d'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


METADATA_TABLE = 'arxivpapermetadatawithtranslatedurlmodel'
BLOG_TABLE = 'blogpostcontentmodel'


def upgrade() -> None:
	# Enable RLS
	op.enable_rls(METADATA_TABLE)
	op.enable_rls(BLOG_TABLE)

	# arxiv metadata: read-only for anon/authenticated
	op.create_rls_policy(
		'metadata_select',
		METADATA_TABLE,
		command='SELECT',
		using='true',
	)

	# blog posts: anyone can read
	op.create_rls_policy(
		'blog_select',
		BLOG_TABLE,
		command='SELECT',
		using='true',
	)
	# blog posts: authenticated users can insert their own
	op.create_rls_policy(
		'blog_insert',
		BLOG_TABLE,
		command='INSERT',
		to='authenticated',
		with_check='auth.uid() = user_id',
	)
	# blog posts: owner can update
	op.create_rls_policy(
		'blog_update',
		BLOG_TABLE,
		command='UPDATE',
		to='authenticated',
		using='auth.uid() = user_id',
		with_check='auth.uid() = user_id',
	)
	# blog posts: owner can delete
	op.create_rls_policy(
		'blog_delete',
		BLOG_TABLE,
		command='DELETE',
		to='authenticated',
		using='auth.uid() = user_id',
	)


def downgrade() -> None:
	op.drop_rls_policy('blog_delete', BLOG_TABLE)
	op.drop_rls_policy('blog_update', BLOG_TABLE)
	op.drop_rls_policy('blog_insert', BLOG_TABLE)
	op.drop_rls_policy('blog_select', BLOG_TABLE)
	op.drop_rls_policy('metadata_select', METADATA_TABLE)

	op.disable_rls(BLOG_TABLE)
	op.disable_rls(METADATA_TABLE)
