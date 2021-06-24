from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base

from db.credentials import DB_PATH

Base = declarative_base()


def generate_engine(
    url: str = DB_PATH,
) -> Engine:
    engine = create_engine(url, echo=True)
    from .User import User
    from .Note import Note

    Base.metadata.create_all(engine)

    return engine
