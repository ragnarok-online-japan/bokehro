import json

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

configure: dict = {}
with open("./config.json") as fp:
    configure = json.load(fp)

sqlalchemy_database_url: str = "{protocol:s}://{username:s}:{password:s}@{hostname:s}/{dbname:s}?charset={charset:s}".\
    format(**configure["sqlalchemy"])

Engine = create_engine(
    sqlalchemy_database_url
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

Base = declarative_base()
