import json
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(base_dir, "../config.json")

configure: dict = {}
with open(config_path) as fp:
    configure = json.load(fp)

sqlalchemy_database_url: str = "{protocol:s}://{username:s}:{password:s}@{hostname:s}/{dbname:s}?charset={charset:s}".\
    format(**configure["sqlalchemy"])

Engine = create_engine(
    sqlalchemy_database_url
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

Base = declarative_base()
