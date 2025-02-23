import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend import config

SQLALCHEMY_DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('POSTGRES_DB')}"


# Create a synchronous engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base model
Base = declarative_base()

Base.metadata.create_all(engine)


# Dependency for getting the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
