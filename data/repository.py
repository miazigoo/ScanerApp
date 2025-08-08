from datetime import datetime

from kivy import logger
from kivy.app import App
from kivy.clock import Clock

from api.api_client import ApiClient
from models.models import BarcodeORM
from data.service import DatabaseService
from models.barcode import Barcode

from data.session import AppSession


class Repository:
    def __init__(self):
        self.db = DatabaseService()
        self.api = ApiClient()
        self._sync_event = None  # Для хранения события синхронизации

    def save_and_send_barcode(self, barcode_data: dict):
        # Проверка дубля
        is_duplicate = self.barcode_exists(
            barcode_data['code'],
            barcode_data['order'],
            barcode_data['stage']
        )
        if is_duplicate:
            return {"success": False, "reason": "duplicate"}

        # Сохраняем
        barcode_id = self.save_barcode(barcode_data)
        if not barcode_id:
            return {"success": False, "reason": "db_error"}

        # Пытаемся отправить
        success = self.send_barcode(barcode_data)
        if success:
            self.db.update(BarcodeORM, barcode_id, {"is_sent": True})
        return {"success": success, "barcode_id": barcode_id}

    def is_barcode_exists(self, code, order, stage):
        # Можно добавить is_good, user_id, если нужно
        return self.db.exists(BarcodeORM, {
            "code": code,
            "order": order,
            "stage": stage,
        })

    def barcode_exists(self, code, order_id, stage_id):
        """
        Проверяет, есть ли уже такой штрихкод для заказа+этапа.
        """
        return self.db.exists(
            BarcodeORM,
            {"code": code, "order": order_id, "stage": stage_id}
        )

    def send_barcode(self, data: dict):
        """Отправляет штрих-код на сервер.
        Args:
            data: Объект штрих-кода (Pydantic модель)
        Returns:
            True, если отправка успешна, иначе False
        """
        try:
            # Отправляем в API
            response = self.api.create_barcode(data)
            return response.get('success', False)
        except Exception as e:
            # Логируем ошибку
            print(f"Repository error: {str(e)}")  # для отладки
            return False

    def save_barcode(self, barcode_data: dict) -> int:
        """
        Сохраняет штрих-код в локальную базу данных.

        Args:
            barcode_data: словарь с данными штрих-кода

        Returns:
            int: ID сохраненной записи
        """
        try:
            return self.db.insert(BarcodeORM, barcode_data)
        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            return None


    def sync_barcode(self):
        """Синхронизирует неотправленные штрих-коды с API.

        Args:
            max_retries: Максимальное количество попыток для одного штрих-кода
        """
        unsynced = self.db.get_unsynced_barcodes()

        for barcode_orm in unsynced:
            barcode = Barcode.model_validate(barcode_orm)
            try:
                # Отправляем в API
                self.api.create_barcode(barcode)
                # Обновляем статус в БД
                self.db.update(
                    BarcodeORM,
                    barcode_orm.id,
                    {"is_sent": True}
                )
                logger.Logger.info(f"Successfully synced barcode {barcode_orm.id}")
            except Exception as e:
                # Логируем ошибку и увеличиваем счетчик
                logger.Logger.error(f"Failed to sync barcode {barcode_orm.id}: {str(e)}")
                self.db.update(
                    BarcodeORM,
                    barcode_orm.id,
                    {"error_count": barcode_orm.error_count +1}
                )

    def start_auto_sync(self, interval: float = 60.0) -> None:
        """Запускает периодическую синхронизацию.

        Args:
            interval: Интервал синхронизации в секундах
        """
        self.stop_auto_sync()  # Останавливаем предыдущую синхронизацию
        self._sync_event = Clock.schedule_interval(
            lambda dt: self.sync_barcode(), interval
        )

    def stop_auto_sync(self) -> None:
        """Останавливает периодическую синхронизацию."""
        if self._sync_event:
            self._sync_event.cancel()
            self._sync_event = None

    def delete_many(self, model, filters=None):
        """Удаляет несколько записей по фильтру и возвращает количество удаленных"""
        return self.db.delete_many(model, filters)