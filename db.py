import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("No database url provided")

engine = create_engine(database_url, echo=True)

session = sessionmaker(bind=engine)

Base = declarative_base()
