import logging
from datetime import datetime

import requests

from data.session import AppSession
from models.barcode import Barcode
from typing import List

from models.order import Order
from models.process_type import ProcessType
from models.user import User


class ApiClient:
    BASE_URL = "http://srv-dnp.argos.loc"    # Prod
    # BASE_URL = "http://127.0.0.1:8000"    # Dev
    def __init__(self):
        self.session = requests.Session()
        self.csrf_token = None

    def login_by_token(self, token: str) -> User:
        data = {"token": token}
        try:
            resp = self.session.post(
                f"{self.BASE_URL}/api/v2/accounts/login/token",
                json=data,
                timeout=5
            )
            resp.raise_for_status()
        except requests.Timeout:
            raise Exception("Превышено время ожидания ответа от сервера")
        except requests.ConnectionError:
            raise Exception("Нет соединения с сервером. Проверьте интернет.")
        except requests.HTTPError as e:
            try:
                msg = resp.json().get("detail") if resp.content else ""
            except Exception:
                msg = resp.text
            raise Exception(f"Ошибка авторизации по токену: {msg}") from e
        except Exception as e:
            raise Exception(f"Ошибка соединения: {e}") from e

        self.csrf_token = resp.cookies.get("csrftoken", None)
        AppSession.csrf_token = self.csrf_token
        print(f"CSRF Token: {self.csrf_token}")
        return User(**resp.json())

    def login(self, username: str, password: str) -> User:
        data = {"username": username, "password": password}
        try:
            resp = self.session.post(
                f"{self.BASE_URL}/api/v2/accounts/login",
                json=data,
                timeout=5
            )
            resp.raise_for_status()
        except requests.Timeout:
            raise Exception("Превышено время ожидания ответа от сервера")
        except requests.ConnectionError:
            raise Exception("Нет соединения с сервером. Проверьте интернет.")
        except requests.HTTPError as e:
            from requests import HTTPError
            try:
                msg = resp.json().get("detail") if resp.content else ""
            except Exception:
                msg = resp.text
            raise Exception(f"Ошибка авторизации: {msg}") from e
        except Exception as e:
            raise Exception(f"Ошибка соединения: {e}") from e

        self.csrf_token = resp.cookies.get("csrftoken", None)
        AppSession.csrf_token = self.csrf_token
        print(f"CSRF Token: {self.csrf_token}")
        return User(**resp.json())

    def get_process_type(self, process_type_id: int) -> ProcessType:
        """Получает информацию о типе процесса и его этапах"""
        resp = self.session.get(
            f"{self.BASE_URL}/api/v2/orders/process-types/{process_type_id}"
        )
        try:
            resp.raise_for_status()
            data = resp.json()
            return ProcessType(**data)
        except requests.HTTPError as e:
            logging.error(f"Ошибка при получении типа процесса: {e}")
            # Можно вывести код ошибки пользователю
            raise Exception(f"Ошибка получения типа процесса (код {resp.status_code}): {resp.text}") from e

    def get_orders(self) -> List[Order]:
        resp = self.session.get(
            f"{self.BASE_URL}/api/v2/orders/orders-filters-for-scaner",
            params={
                "order_by": "-name",
                "using_barcode": True
            }
        )
        try:
            resp.raise_for_status()
            orders_data = resp.json()

            orders = []

            for order_data in orders_data:
                order = Order(**order_data)

                orders.append(order)

            return orders
        except requests.HTTPError as e:
            logging.error(f"Ошибка при выполнении запроса: {e}")
            logging.error(f"Ответ сервера: {resp.text}")
            raise Exception("Ошибка выполнения API-запроса") from e

    def get_process_types(self) -> List[ProcessType]:
        resp = self.session.get(
            f"{self.BASE_URL}/api/v2/orders/process-types",   # new api fron ninja
            # f"{self.BASE_URL}/api/dnp/orders/process-types",   # old api from drf
            params={"order_by": "-name", "using_barcode": True}
        )
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logging.error(f"Ошибка при выполнении запроса: {e}")
            raise Exception("Ошибка выполнения API-запроса") from e

        return [ProcessType(**pt) for pt in resp.json()]

    def create_barcode(self, data: dict):
        # Убедимся, что created_at в правильном формате
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        headers = {
            "X-CSRFToken": AppSession.csrf_token,
            "Content-Type": "application/json"
        }

        try:
            resp = self.session.post(
                f"{self.BASE_URL}/api/v2/barcode/import-barcode",
                json=data,
                headers=headers,
                timeout=3
            )
            print(resp.text)
            resp.raise_for_status()
            return resp.json()
        except requests.Timeout:
            raise Exception("Превышено время ожидания ответа сервера")
        except requests.ConnectionError:
            raise Exception("Ошибка подключения к серверу")
        except Exception as e:
            print(f"API error: {str(e)}")
            return {"success": False, "error": str(e)}

    def sent_barcodes(self, barcodes: List[Barcode]):
        """Отправляет список штрих-кодов на сервер.

        Args:
            barcodes: Список объектов Barcode для отправки

        Returns:
            Ответ сервера в формате JSON

        Raises:
            Exception: Если произошла ошибка HTTP или другая ошибка
        """
        headers = {
            "X-CSRFToken": self.csrf_token,
            "Content-Type": "application/json"
        } if self.csrf_token else {"Content-Type": "application/json"}
        # Конвертируем список моделей в список словарей
        data = [barcode.model_dump(exclude_unset=True) for barcode in barcodes]
        try:
            resp = self.session.post(
                f"{self.BASE_URL}/api/v2/barcode/import-barcodes",
                json=data,
                headers=headers
            )
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            error_msg = f"Ошибка HTTP {e.response.status_code}: {e.response.text}"
            logging.error(error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            logging.error(f"Ошибка при отправке штрих-кодов: {str(e)}")
            raise

    def get_order_by_id(self, order_id: int):
        """Получает заказ по ID с сервера"""
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/api/v2/orders/{order_id}",
                timeout=5
            )
            resp.raise_for_status()
            return resp.json()  # или Order(**resp.json()), если используете модель
        except requests.Timeout:
            raise Exception("Превышено время ожидания ответа от сервера")
        except requests.ConnectionError:
            raise Exception("Нет соединения с сервером. Проверьте интернет.")
        except requests.HTTPError as e:
            from requests import HTTPError
            try:
                msg = resp.json().get("detail") if resp.content else ""
            except Exception:
                msg = resp.text
            raise Exception(f"Ошибка получения заказа: {msg}") from e
        except Exception as e:
            raise Exception(f"Ошибка соединения: {e}") from e
