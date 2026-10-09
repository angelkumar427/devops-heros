from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import database_url


class Base(DeclarativeBase):
    pass


engine = create_engine(database_url(), pool_pre_ping=True)

if engine.dialect.name == "sqlite":  # test database: SQLite only enforces foreign keys when asked
    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
