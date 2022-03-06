from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.db.config import config

if config.DATABASE_URL is None:
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{config.pg_username}:{config.pg_password}@{config.pg_host}:{config.pg_port}/{config.db_name}"
    )
else:
    SQLALCHEMY_DATABASE_URI = config.DATABASE_URL
    
print(SQLALCHEMY_DATABASE_URI)

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
