import os
from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

# Load environment variables from .env file
load_dotenv()

def create_engine():
    """
    Create and return a SQLAlchemy engine using environment variables.
    """
    connection_string = (
        f"mssql+pyodbc://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@"
        f"{os.getenv('DATABASE_SERVER')}/{os.getenv('DATABASE_NAME')}?"
        f"driver={os.getenv('DATABASE_DRIVER')}"
    )
    return sa.create_engine(connection_string)

def create_session():
    """
    Create and return a SQLAlchemy session.
    """
    engine = create_engine()
    Session = sessionmaker(bind=engine)
    return Session()
