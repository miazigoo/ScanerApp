import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine



SQL_DB_URL = "sqlite:///db.sqlite3"

# Включаем логирование SQL-запросов
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

engine = create_engine(
    SQL_DB_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
