from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    return create_engine(
        get_settings().database_url.get_secret_value(), pool_pre_ping=True, hide_parameters=True
    )


def get_db():
    # Routes own the transaction. Any exception rolls back on session close.
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session
