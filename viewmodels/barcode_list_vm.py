import os
from datetime import datetime
from typing import List

from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivymd.uix.boxlayout import MDBoxLayout
import json

from models.models import BarcodeORM, OrderORM
from data.repository import Repository
from models.barcode import Barcode


class BarcodeItem(MDBoxLayout):
    id = NumericProperty()
    code = StringProperty()
    is_sent = BooleanProperty()
    created_at = StringProperty()
    error_count = NumericProperty()


class BarcodeListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._progress_popup = None
        self._current_operation = None
        self._is_data_updated = False  # Флаг для отслеживания обновлений данных

    def _show_progress_popup(self, title: str, max_value: int):
        """Создаёт popup с прогресс-баром."""
        layout = BoxLayout(orientation='vertical', spacing=10)
        self._progress_bar = ProgressBar(max=max_value)
        layout.add_widget(Label(text=title))
        layout.add_widget(self._progress_bar)

        self._progress_popup = Popup(
            title="Отправка данных",
            content=layout,
            size_hint=(0.8, 0.3)
        )
        self._progress_popup.open()

    def _update_progress(self, value: int):
        """Обновляет прогресс-бар."""
        if self._progress_popup:
            self._progress_bar.value = value

    def _close_progress_popup(self):
        """Закрывает popup с прогресс-баром."""
        if self._progress_popup:
            self._progress_popup.dismiss()
            self._progress_popup = None

    def on_pre_enter(self):
        self.update_unsynced_count()
        self.load_barcode()

    def update_unsynced_count(self):
        """Обновляет информацию о неотправленных штрих-кодах"""
        repo = Repository()
        unsynced = repo.db.get_unsynced_barcodes()

        # Группируем по заказам
        orders = {}
        for barcode in unsynced:
            order_id = barcode["order"]
            if order_id not in orders:
                orders[order_id] = {
                    "count": 0,
                    "name": self._get_order_name(order_id)
                }
            orders[order_id]["count"] += 1

        # Формируем текст для отображения
        if not orders:
            self.ids.unsynced_info.text = "Все штрих-коды синхронизированы"
        else:
            text = ""
            for order_id, data in orders.items():
                text += f"Заказ: {data['name']} Не отправлено: {data['count']}\n"
            self.ids.unsynced_info.text = text.strip()

    def _get_order_name(self, order_id):
        repo = Repository()
        order = repo.db.get_one(OrderORM, {"id": order_id})
        if order:
            name = order.get("name") if isinstance(order, dict) else getattr(order, "name", None)
            if name:
                return name

        # Если не нашли в локальной БД — пробуем запросить с сервера
        try:
            api_order = repo.api.get_order_by_id(order_id)
            if api_order and "name" in api_order:
                return api_order["name"]
        except Exception as e:
            print(f"Ошибка получения заказа с сервера: {e}")

        return f"ID:{order_id}"

    def load_barcode(self):
        from data.session import AppSession
        repo = Repository()
        current_order = getattr(AppSession, "order", None)

        if current_order:
            # Фильтруем по выбранному заказу
            filters = {"order": current_order.id}
            barcodes = repo.db.get_all(BarcodeORM, filters=filters)
            self.ids.barcode_rv.data = [
                {
                    "id": b["id"],
                    "code": b["code"],
                    "is_sent": b["is_sent"],
                    "created_at": b["created_at"].strftime("%Y-%m-%d %H:%M:%S") if b["created_at"] else "",
                    "error_count": b["error_count"],
                }
                for b in barcodes
            ]
            self.ids.order_filter_label.text = f"Фильтр: {current_order.name}"
        else:
            # Показываем все записи
            barcodes = repo.db.get_all(BarcodeORM)
            self.ids.barcode_rv.data = [
                {
                    "id": b["id"],
                    "code": b["code"],
                    "is_sent": b["is_sent"],
                    "created_at": b["created_at"].strftime("%Y-%m-%d %H:%M:%S") if b["created_at"] else "",
                    "error_count": b["error_count"],
                }
                for b in barcodes
            ]
            self.ids.order_filter_label.text = "Фильтр: все заказы"

    def sync_all(self):
        from threading import Thread
        repo = Repository()
        unsynced = repo.db.get_unsynced_barcodes()
        total = len(unsynced)
        if total == 0:
            self._show_message("Нет данных для отправки")
            return

        self._show_progress_popup("Синхронизация...", total)
        ok_count = 0
        fail_count = 0

        def sync_thread():
            nonlocal ok_count, fail_count
            for idx, barcode_orm in enumerate(unsynced):
                barcode_data = {
                    "code": barcode_orm["code"],
                    "order": barcode_orm["order"],
                    "user_id": barcode_orm["user_id"],
                    "stage": barcode_orm["stage"],
                    "is_good": barcode_orm["is_good"],
                    "created_at": barcode_orm["created_at"],
                    "is_sent": False,
                    "error_count": barcode_orm["error_count"],
                }
                try:
                    success = repo.send_barcode(barcode_data)
                    if success:
                        repo.db.update(BarcodeORM, barcode_orm["id"], {"is_sent": True, "error_count": 0})
                        ok_count += 1
                    else:
                        repo.db.update(BarcodeORM, barcode_orm["id"], {"error_count": barcode_orm["error_count"] + 1})
                        fail_count += 1
                except Exception:
                    repo.db.update(BarcodeORM, barcode_orm["id"], {"error_count": barcode_orm["error_count"] + 1})
                    fail_count += 1
                # Прогрессбар
                Clock.schedule_once(lambda dt, val=idx + 1: self._update_progress(val))

            def after_sync(dt):
                self._close_progress_popup()
                self.load_barcode()
                msg = f"Синхронизировано: {ok_count}\nОшибок: {fail_count}"
                self._show_message(msg)

            Clock.schedule_once(after_sync)

        Thread(target=sync_thread, daemon=True).start()

    def export_json(self):
        repo = Repository()
        barcodes = repo.db.get_unsynced_barcodes()
        total = len(barcodes)
        if total == 0:
            self._show_message("Нет данных для экспорта")
            return

        # Показываем прогресс-бар
        self._show_progress_popup("Экспорт в JSON...", total)
        data = []
        filename = None

        def export_thread():
            nonlocal filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"barcodes_export_{timestamp}.json"
            os.makedirs("exports", exist_ok=True)
            filename = os.path.join("exports", filename)
            counter = 1
            while os.path.exists(filename):
                filename = f"barcodes_export_{timestamp}_{counter}.json"
                counter += 1

            for idx, barcode in enumerate(barcodes):
                item = {
                    "Id": barcode["id"],
                    "Code": barcode["code"],
                    "CreatedAt": barcode["created_at"].isoformat() if barcode["created_at"] else None,
                    "User": barcode["user_id"],
                    "Order": barcode["order"],
                    "Stage": barcode["stage"],
                    "IsGood": barcode["is_good"],
                    "IsSent": barcode["is_sent"],
                    "ErrorCount": barcode["error_count"]
                }
                data.append(item)
                # обновляем прогресс
                Clock.schedule_once(lambda dt, val=idx + 1: self._update_progress(val))
            # Сохраняем файл
            with open(filename, "w", encoding="utf-8") as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False, default=str)

            def after_export(dt):
                self._close_progress_popup()
                self._show_message(f"Экспорт завершён:\n{filename}")

            Clock.schedule_once(after_export)

        from threading import Thread
        Thread(target=export_thread, daemon=True).start()

    def _show_message(self, text: str):
        """Показывает всплывающее сообщение."""
        Popup(
            title="Результат",
            content=Label(text=text),
            size_hint=(0.8, 0.3)
        ).open()

    def on_barcode_item_click(self, barcode_item):
        # Показываем popup с кнопками
        from kivymd.uix.button import MDRaisedButton
        layout = BoxLayout(orientation="vertical", spacing=8)
        layout.add_widget(Label(
            text=f"ID: {barcode_item.id}\nШтрихкод: {barcode_item.code}\nСтатус: {'Отправлен' if barcode_item.is_sent else 'Не отправлен'}"))
        layout.add_widget(Label(
            text=f"Штрихкод: {barcode_item.code}\nСтатус: {'Отправлен' if barcode_item.is_sent else 'Не отправлен'}"))
        btn_send = MDRaisedButton(text="Отправить", on_release=lambda x: self._try_send_one(barcode_item))
        btn_delete = MDRaisedButton(text="Удалить", on_release=lambda x: self._delete_one(barcode_item))
        layout.add_widget(btn_send)
        layout.add_widget(btn_delete)
        popup = Popup(title="Действие", content=layout, size_hint=(.7, .4))
        self._select_popup = popup
        popup.open()

    def _try_send_one(self, barcode_item):
        self._select_popup.dismiss()
        from threading import Thread
        repo = Repository()

        def send_thread():
            obj = repo.db.get_one(BarcodeORM, {"id": barcode_item.id})  # теперь obj — dict!
            if not obj:
                Clock.schedule_once(lambda dt: self._show_message("Не найден в БД"))
                return
            data = {
                "code": obj["code"],
                "order": obj["order"],
                "user_id": obj["user_id"],
                "stage": obj["stage"],
                "is_good": obj["is_good"],
                "created_at": obj["created_at"],
                "is_sent": False,
                "error_count": obj["error_count"],
            }
            try:
                success = repo.send_barcode(data)
                if success:
                    repo.db.update(BarcodeORM, obj["id"], {"is_sent": True, "error_count": 0})
                    msg = "Успешно отправлено"
                else:
                    repo.db.update(BarcodeORM, obj["id"], {"error_count": obj["error_count"] + 1})
                    msg = "Ошибка при отправке"
            except Exception as e:
                repo.db.update(BarcodeORM, obj["id"], {"error_count": obj["error_count"] + 1})
                msg = f"Ошибка: {str(e)}"
            Clock.schedule_once(lambda dt: (self.load_barcode(), self._show_message(msg)))

        Thread(target=send_thread, daemon=True).start()

    def _delete_one(self, barcode_item):
        self._select_popup.dismiss()
        repo = Repository()
        obj = repo.db.get_one(BarcodeORM, {"id": barcode_item.id})  # теперь obj — dict!
        if obj:
            repo.db.delete(BarcodeORM, obj["id"])
            self.load_barcode()
            self._show_message("Удалено")
        else:
            self._show_message("Не найден в БД")

    def clear_history(self):
        """Удаляет все отправленные записи (is_sent=True)"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        # Диалог подтверждения
        self._confirm_dialog = MDDialog(
            title="Очистка истории",
            text="Удалить все отправленные штрих-коды? Это действие нельзя отменить.",
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self._confirm_dialog.dismiss()
                ),
                MDFlatButton(
                    text="УДАЛИТЬ",
                    on_release=lambda x: self._perform_clear_history()
                ),
            ],
        )
        self._confirm_dialog.open()

    def _perform_clear_history(self):
        """Выполняет очистку истории после подтверждения"""
        self._confirm_dialog.dismiss()
        repo = Repository()

        # Удаляем только отправленные записи
        deleted_count = repo.db.delete_many(BarcodeORM, {"is_sent": True})

        # Обновляем список
        self.load_barcode()
        self._show_message(f"Удалено записей: {deleted_count}")



