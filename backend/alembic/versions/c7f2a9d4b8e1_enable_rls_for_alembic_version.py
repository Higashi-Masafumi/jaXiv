"""enable_rls_for_alembic_version

Revision ID: c7f2a9d4b8e1
Revises: 3b1e9f4d2a7c
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'c7f2a9d4b8e1'
down_revision: Union[str, Sequence[str], None] = '3b1e9f4d2a7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ALEMBIC_VERSION_TABLE = 'alembic_version'


def upgrade() -> None:
	op.enable_rls(ALEMBIC_VERSION_TABLE)


def downgrade() -> None:
	op.disable_rls(ALEMBIC_VERSION_TABLE)
