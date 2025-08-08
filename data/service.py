"""
Универсальный сервис для работы с БД

Содержит CRUD-операции для всех моделей:
- BarcodeORM
- UserORM
- OrderORM
- ProcessTypeORM
- SessionORM
- LoginToken

Примеры использования:
    # Вставка данных
    db_service = DatabaseService()
    db_service.insert(BarcodeORM, {"code": "123", "order": 1})

    # Чтение данных
    unsynced_barcodes = db_service.get_all(BarcodeORM, filters={"is_sent": False})
"""

from contextlib import contextmanager
from typing import Type, Any, Dict, List, Optional, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from data.db import SessionLocal
from models.models import Base, BarcodeORM


T = TypeVar('T', bound=Base)


class DatabaseService:
    def __init__(self):
        self.session_local =SessionLocal

    @contextmanager
    def _session_scope(self) -> Session:
        """Контекстный менеджер для безопасной работы с сессиями"""
        session = self.session_local()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def insert(self, model: Type[T], data: Union[Dict[str, Any], T]) -> int:
        """Добавление новой записи"""
        with self._session_scope() as session:
            obj = model(**data)
            session.add(obj)
            session.flush()
            return obj.id

    def get_all(
            self,
            model: Type[T],
            filters: Optional[Dict[str, Any]] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            order_by: Optional[str] = None
    ) -> List[Base]:
        """Получение всех записей с фильтрацией"""
        with self._session_scope() as session:
            query = session.query(model)
            if filters:
                query = query.filter_by(**filters)
            if order_by:
                if order_by.startswith('-'):
                    query = query.order_by(getattr(model, order_by[1:]).desc())
                else:
                    query = query.order_by(getattr(model, order_by))
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            results = query.all()
            return [self.orm_to_dict(obj) for obj in results]

    @staticmethod
    def orm_to_dict(obj):
        """Преобразует ORM-объект в dict вручную"""
        # Можно еще сделать универсально через __table__.columns
        return {col.name: getattr(obj, col.name) for col in obj.__table__.columns}

    def update(
            self,
            model: Type[T],
            id: int,
            data: Dict[str, Any],
    ) -> bool:
        """Обновление записи"""
        with self._session_scope() as session:
            obj = session.query(model).get(id)
            if not obj:
                return False
            for key, value in data.items():
                setattr(obj, key, value)
            return True

    def delete(self, model: Type[T], id: int) -> bool:
        """Удаление записи"""
        with self._session_scope() as session:
            obj = session.query(model).get(id)
            if not obj:
                return False
            session.delete(obj)
            return True

    def delete_many(self, model: Type[T], filters: Optional[Dict[str, Any]] = None) -> int:
        """Удаляет несколько записей по фильтру и возвращает количество удаленных"""
        with self._session_scope() as session:
            query = session.query(model)
            if filters:
                query = query.filter_by(**filters)
            count = query.count()  # Получаем количество перед удалением
            query.delete(synchronize_session=False)
            return count

    def get_columns(self, model: Type[Base]) -> List[str]:
        """Получение списка колонок модели"""
        return [column.key for column in inspect(model).columns]

    def get_one(self, model: Type[T], filters: Dict[str, Any]) -> Optional[dict]:
        """Получение одной записи по фильтру"""
        with self._session_scope() as session:
            obj = session.query(model).filter_by(**filters).first()
            return self.orm_to_dict(obj) if obj else None

    def get_unsynced_barcodes(self):
        """Получение всех несинхронизированных штрих-кодов"""
        with self._session_scope() as session:
            return [self.orm_to_dict(obj) for obj in session.query(BarcodeORM).filter_by(is_sent=False).all()]

    def bulk_insert(self, model: Type[T], data_list: List[Dict[str, Any]]) -> List[int]:
        """Массовая вставка записей"""
        with self._session_scope() as session:
            objects = [model(**data) for data in data_list]
            session.bulk_save_objects(objects)
            session.flush()
            return [obj.id for obj in objects if hasattr(obj, 'id')]

    def exists(self, model: Type[T], filters: Dict[str, Any]) -> bool:
        """Проверка существования записи"""
        with self._session_scope() as session:
            return session.query(
                session.query(model).filter_by(**filters).exists()
            ).scalar()
