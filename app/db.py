""" Database utilities for the application. """
import os
from sqlmodel import SQLModel, create_engine, Session
from app.config import settings

DATABASE_URL = settings.database_url


# Create data directory if using sqlite and directory doesn't exist
if DATABASE_URL.startswith("sqlite:///"):
    # Extract the file path from the DATABASE_URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]  # Remove the "./" prefix

    # Get the directory path
    db_dir = os.path.dirname(db_path)

    # Create the directory if it doesn't exist and is not empty
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"Created directory: {db_dir}")

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    """ Get a session for the database. """
    with Session(engine) as session:
        yield session


def init_db():
    """ Initialize the database. """
    SQLModel.metadata.create_all(engine)
