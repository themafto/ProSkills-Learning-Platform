from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import config

SQLALCHEMY_DATABASE_URL = "postgresql://{}:{}@{}:{}/{}".format(
    config.POSTGRES_USER,
    config.POSTGRES_PASSWORD,
    config.POSTGRES_HOST,
    config.DATABASE_PORT,
    config.POSTGRES_DB,
)

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
