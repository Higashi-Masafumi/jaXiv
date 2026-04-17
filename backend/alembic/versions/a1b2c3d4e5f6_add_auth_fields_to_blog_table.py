"""add_auth_fields_to_blog_table

Revision ID: a1b2c3d4e5f6
Revises: 91c1b44c9807
Create Date: 2026-04-15 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '91c1b44c9807'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	"""Add source_type and user_id columns for Supabase auth support."""
	op.add_column(
		'blogpostcontentmodel',
		sa.Column(
			'source_type',
			sa.String(10),
			nullable=False,
			server_default='arxiv',
		),
	)
	op.add_column(
		'blogpostcontentmodel',
		sa.Column('user_id', UUID(as_uuid=True), nullable=True),
	)


def downgrade() -> None:
	"""Remove source_type and user_id columns."""
	op.drop_column('blogpostcontentmodel', 'user_id')
	op.drop_column('blogpostcontentmodel', 'source_type')
