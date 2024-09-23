from sqlalchemy import create_engine, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeBase, mapped_column, Mapped
from data import MYSQL_USER, MYSQL_DB, MYSQL_HOST, MYSQL_PORT, MYSQL_PASSWORD
from sqlalchemy.types import JSON
import atexit
from datetime import datetime

SQLALCHEMY_DSN = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(MYSQL_USER,
                                                             MYSQL_PASSWORD,
                                                             MYSQL_HOST,
                                                             MYSQL_PORT,
                                                             MYSQL_DB)

engine = create_engine(SQLALCHEMY_DSN)

# Определение модели
class Base(DeclarativeBase):
    pass


class AddedAddresses(Base):
    __tablename__ = 'addedAddresses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    house_id: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[list] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now())

class Address(Base):
    __tablename__ = 'badAddresses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    house_id: Mapped[int] = mapped_column(Integer,  nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    search_service: Mapped[list] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now())

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print("Ошибка при создании таблицы:", e)

try:
    # Создание класса Session, который можно будет использовать для создания сессий
    Session = sessionmaker(bind=engine)
except Exception as e:
    print("Ошибка при создании сессии:", e)
    Session = None


# Автоматическое закрытие соединения при завершении программы
atexit.register(engine.dispose)