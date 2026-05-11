"""add_user_subscription

Revision ID: d9e2f1a3b4c5
Revises: c7f2a9d4b8e1
Create Date: 2026-04-30 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'd9e2f1a3b4c5'
down_revision: Union[str, Sequence[str], None] = 'c7f2a9d4b8e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SUBSCRIPTION_TABLE = 'user_subscription'


def upgrade() -> None:
	op.create_table(
		SUBSCRIPTION_TABLE,
		sa.Column('user_id', UUID(as_uuid=True), primary_key=True),
		sa.Column(
			'plan',
			sa.String(length=16),
			nullable=False,
			server_default='free',
		),
		sa.Column('stripe_customer_id', sa.Text(), nullable=True),
		sa.Column('stripe_subscription_id', sa.Text(), nullable=True),
		sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
		sa.Column(
			'cancel_at_period_end',
			sa.Boolean(),
			nullable=False,
			server_default=sa.text('false'),
		),
		sa.Column(
			'created_at',
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.text('NOW()'),
		),
		sa.Column(
			'updated_at',
			sa.DateTime(timezone=True),
			nullable=False,
			server_default=sa.text('NOW()'),
		),
		sa.CheckConstraint(
			"plan IN ('free', 'paid')",
			name='user_subscription_plan_check',
		),
	)
	op.create_index(
		'ix_user_subscription_stripe_customer_id',
		SUBSCRIPTION_TABLE,
		['stripe_customer_id'],
		unique=True,
		postgresql_where=sa.text('stripe_customer_id IS NOT NULL'),
	)

	op.enable_rls(SUBSCRIPTION_TABLE)
	# Subscriptions are owned by their user; selectable by the user.
	op.create_rls_policy(
		'user_subscription_select',
		SUBSCRIPTION_TABLE,
		command='SELECT',
		to='authenticated',
		using='auth.uid() = user_id',
	)
	# Writes are restricted to the service role (backend).
	# (No INSERT/UPDATE/DELETE policy is granted to authenticated users.)


def downgrade() -> None:
	op.drop_rls_policy('user_subscription_select', SUBSCRIPTION_TABLE)
	op.disable_rls(SUBSCRIPTION_TABLE)
	op.drop_index(
		'ix_user_subscription_stripe_customer_id',
		table_name=SUBSCRIPTION_TABLE,
	)
	op.drop_table(SUBSCRIPTION_TABLE)
