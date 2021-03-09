from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from updblaster import local_settings

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"
if local_settings.DEBUG:
    SQLALCHEMY_DATABASE_URL = "mysql://rd:RandD268@127.0.0.1:23306/blasterdb"
else:
    SQLALCHEMY_DATABASE_URL = "mysql://rd:RandD268@127.0.0.1:3306/blasterdb"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
