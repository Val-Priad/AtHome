import os
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None


def create_db_engine(database_url: str):
    return create_engine(database_url)


def create_session_factory(engine: Engine):
    return sessionmaker(
        bind=engine,
    )


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL is not set")

        _engine = create_db_engine(database_url)

    return _engine


def get_session() -> Session:
    global _SessionFactory

    if not _SessionFactory:
        _SessionFactory = create_session_factory(get_engine())
    return _SessionFactory()


@contextmanager
def db_session():
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
