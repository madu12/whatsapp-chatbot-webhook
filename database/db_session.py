import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL


# Load environment variables from .env file
load_dotenv()

def create_engine():
    """
    Create and return a SQLAlchemy engine using environment variables.
    """
    try:
        connection_string = (
                f"Driver={os.getenv('DATABASE_DRIVER')};"
                f"Server={os.getenv('DATABASE_SERVER')};"
                f"Database={os.getenv('DATABASE_NAME')};"
                f"Uid={os.getenv('DATABASE_USERNAME')};"
                f"Pwd={os.getenv('DATABASE_PASSWORD')};"
                f"Encrypt=no;TrustServerCertificate=yes;Connection Timeout=30;"
            )
        connection_url = URL.create(
            "mssql+pyodbc",
            query={"odbc_connect": connection_string}
        )
        engine = sa.create_engine(connection_url)
        return engine
    except Exception as e:
        print(f"Error creating engine: {e}")
        raise e

def create_session():
    """
    Create and return a SQLAlchemy session.
    """
    engine = create_engine()
    Session = sessionmaker(bind=engine)
    return Session()