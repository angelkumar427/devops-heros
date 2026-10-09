from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool, text

from app.config import database_url
from app.db import Base
from app import models  # noqa: F401 - registers the tables on Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Every backend replica runs "alembic upgrade head" on start. Without a lock, two pods starting
# together would both try to create the same tables. A Postgres advisory lock makes the second
# pod wait until the first has finished, then find nothing left to do.
MIGRATION_LOCK_ID = 7_210_421


def run_migrations_offline() -> None:
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        is_pg = connection.dialect.name == "postgresql"
        if is_pg:
            connection.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            connection.commit()
        try:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if is_pg:
                connection.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
