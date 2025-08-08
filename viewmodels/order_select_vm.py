
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.behaviors import HoverBehavior

from data.repository import Repository
from data.session import AppSession
from kivymd.uix.list import OneLineAvatarIconListItem

from models.process_type import ProcessType


# Класс для RecycleView, чтобы работал индикатор выбора
class OrderListItem(HoverBehavior, OneLineAvatarIconListItem):
    order_id = NumericProperty(0)
    name = StringProperty("")
    is_selected = BooleanProperty(False)
    hovered = BooleanProperty(False)


class OrderSelectScreen(Screen):
    all_orders = []
    selected_order_id = None

    def on_pre_enter(self):
        repo = Repository()
        try:
            orders = repo.api.get_orders()
            print("Полученные заказы:")
            for order in orders:
                print(f"Order ID: {order.id}")
                print(f"Order Name: {order.name}")
                print(f"Process Type ID: {order.process_type_id}")
                print(f"Process Type: {order.process_type}")
                if isinstance(order.process_type, ProcessType):
                    print(f"Stages: {order.process_type.stages}")
                print("---")

            self.all_orders = orders
            self.update_orders_view(orders)
        except Exception as e:
            print(f"Error loading orders: {e}")

    def filter_orders(self, search_text):
        """Фильтруем список заказов по тексту поиска."""
        filtered = [
            order for order in self.all_orders
            if search_text.lower() in order.name.lower()
        ]
        filtered = sorted(filtered, key=lambda o: o.name)  # сортировка
        self.update_orders_view(filtered)

    def update_orders_view(self, orders):
        self.ids.order_rv.data = [
            {
                "order_id": order.id,
                "text": order.name,  # <-- вот это обязательно!
                "is_selected": (order.id == self.selected_order_id)
            }
            for order in orders
        ]

    def select_order(self, order_id):
        self.manager.current = "order_select"
        order = next((order for order in self.all_orders if order.id == order_id), None)
        if order:
            print(f"Selecting order ID: {order.id}")
            print(f"Order name: {order.name}")
            print(f"Process type ID: {order.process_type_id}")
            AppSession.order = order
            self.selected_order_id = order.id
            self.filter_orders(self.ids.search_field.text)

            # Проверяем наличие process_type и stages
            if isinstance(order.process_type, ProcessType):
                print(f"Process type: {order.process_type.dict()}")
                if order.process_type.stages:
                    print(f"Available stages: {[s.dict() for s in order.process_type.stages]}")

            main_screen = self.manager.get_screen("main")
            if hasattr(main_screen, "on_pre_enter"):
                main_screen.on_pre_enter()
            self.manager.current = "main"

