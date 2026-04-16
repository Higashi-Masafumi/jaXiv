import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from alembic import context
from alembic.operations import MigrateOperation, Operations
from infrastructure.postgres.models import SQLModel

load_dotenv()

# region RLS Operations


@Operations.register_operation('enable_rls')
class EnableRLSOp(MigrateOperation):
    def __init__(self, table_name: str, *, force: bool = False) -> None:
        self.table_name = table_name
        self.force = force

    @classmethod
    def enable_rls(cls, operations: Operations, table_name: str, **kw: object) -> None:
        operations.invoke(cls(table_name, **kw))


@Operations.implementation_for(EnableRLSOp)
def _(operations: Operations, op: EnableRLSOp) -> None:
    operations.execute(f'ALTER TABLE {op.table_name} ENABLE ROW LEVEL SECURITY')
    if op.force:
        operations.execute(f'ALTER TABLE {op.table_name} FORCE ROW LEVEL SECURITY')


@Operations.register_operation('disable_rls')
class DisableRLSOp(MigrateOperation):
    def __init__(self, table_name: str) -> None:
        self.table_name = table_name

    @classmethod
    def disable_rls(cls, operations: Operations, table_name: str) -> None:
        operations.invoke(cls(table_name))


@Operations.implementation_for(DisableRLSOp)
def _(operations: Operations, op: DisableRLSOp) -> None:
    operations.execute(f'ALTER TABLE {op.table_name} DISABLE ROW LEVEL SECURITY')


@Operations.register_operation('create_rls_policy')
class CreateRLSPolicyOp(MigrateOperation):
    def __init__(
        self,
        policy_name: str,
        table_name: str,
        *,
        using: str | None = None,
        with_check: str | None = None,
        command: str = 'ALL',
        to: str = 'public',
    ) -> None:
        self.policy_name = policy_name
        self.table_name = table_name
        self.using = using
        self.with_check = with_check
        self.command = command
        self.to = to

    @classmethod
    def create_rls_policy(
        cls, operations: Operations, policy_name: str, table_name: str, **kw: object
    ) -> None:
        operations.invoke(cls(policy_name, table_name, **kw))


@Operations.implementation_for(CreateRLSPolicyOp)
def _(operations: Operations, op: CreateRLSPolicyOp) -> None:
    role = 'PUBLIC' if op.to == 'public' else op.to
    sql = f'CREATE POLICY {op.policy_name} ON {op.table_name} FOR {op.command} TO {role}'
    if op.using:
        sql += f' USING ({op.using})'
    if op.with_check:
        sql += f' WITH CHECK ({op.with_check})'
    operations.execute(sql)


@Operations.register_operation('drop_rls_policy')
class DropRLSPolicyOp(MigrateOperation):
    def __init__(self, policy_name: str, table_name: str) -> None:
        self.policy_name = policy_name
        self.table_name = table_name

    @classmethod
    def drop_rls_policy(cls, operations: Operations, policy_name: str, table_name: str) -> None:
        operations.invoke(cls(policy_name, table_name))


@Operations.implementation_for(DropRLSPolicyOp)
def _(operations: Operations, op: DropRLSPolicyOp) -> None:
    operations.execute(f'DROP POLICY {op.policy_name} ON {op.table_name}')


# endregion

config = context.config
postgres_url = os.getenv('POSTGRES_URL')
print(f'postgres_url: {postgres_url}')
if postgres_url is not None:
    config.set_main_option('sqlalchemy.url', postgres_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
