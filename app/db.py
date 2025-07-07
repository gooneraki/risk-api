""" Database utilities for the application. """
import os
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    """ Get a session for the database. """
    with Session(engine) as session:
        yield session


def init_db():
    """ Initialize the database. """
    SQLModel.metadata.create_all(engine)
