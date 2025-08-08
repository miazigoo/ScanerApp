from kivy.animation import Animation
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.clock import Clock

from data.repository import Repository
from data.session import AppSession
from models.barcode import Barcode
from datetime import datetime

from models.models import BarcodeORM
from utils.stage_button import StageButton


class MainScreen(Screen):
    user_display = StringProperty("не выбран")
    order_display = StringProperty("не выбран")
    stage_display = StringProperty("не выбран")
    status_color = ListProperty([0, 0.5, 0, 1])
    is_good_state = BooleanProperty(True)

    def on_pre_enter(self, *args):
        user = getattr(AppSession, "user", None)
        self.user_display = user.username if user else "не выбран"
        order = getattr(AppSession, "order", None)
        self.order_display = order.name if order else "не выбран"
        stage = getattr(AppSession, "stage", None)
        self.stage_display = stage.name if stage else "не выбран"
        try:
            self.ids.barcode_input.text = ""
        except AttributeError:
            pass
        try:
            self.ids.save_status.text = ""
        except AttributeError:
            pass
        self.status_color = [0, 0.5, 0, 1]
        Clock.schedule_once(lambda dt: self.focus_barcode(), 0)  # Фокус после инициализации


    def change_user(self):
        self.manager.current = "login"

    def select_order(self):
        self.manager.current = "order_select"

    def select_stage(self):
        order = getattr(AppSession, "order", None)
        app = App.get_running_app()
        if not order or not hasattr(order, "process_type"):
            self.show_status("Сначала выберите заказ!", error=True)
            return

        repo = Repository()
        process_type = repo.api.get_process_type(order.get_process_type_id())
        stages = getattr(process_type, "stages", [])
        if not stages:
            self.show_status("Для заказа нет этапов", error=True)
            return

        from kivy.uix.popup import Popup
        from kivy.uix.button import Button
        from kivy.uix.boxlayout import BoxLayout
        popup = Popup(title="Выберите этап", size_hint=(.5, .95))
        layout = BoxLayout(
            orientation='vertical',
            spacing=dp(6),
            padding=dp(8),
            size_hint=(1, 1)  # Растягиваем на всю ширину Popup
        )
        popup.content = layout

        for stage in stages:
            btn = StageButton(
                text=stage.name,
                size_hint_y=None,
                height=StageButton.normal_height,
                halign="center",
                valign = "center",
            )
            btn.md_bg_color = btn.get_bg_normal()
            btn.text_color = 'black'
            btn.bind(on_release=lambda btn, s=stage: self._set_stage(s))
            layout.add_widget(btn)
        self._stage_popup = popup
        popup.open()

    def _set_stage(self, stage):
        AppSession.stage = stage
        self.stage_display = stage.name
        self.is_good_state = True

        # Обновляем кнопку состояния
        self.update_state_button()

        # Запуск анимации
        self.animate_stage_card()

        if hasattr(self, "_stage_popup"):
            self._stage_popup.dismiss()
            Clock.schedule_once(lambda dt: self.focus_barcode(), 0.2)

    def animate_stage_card(self):
        card = self.ids.get('stage_card', None)
        if card:
            orig_color = card.md_bg_color if hasattr(card, 'md_bg_color') else (1, 1, 1, 1)
            # на короткое время — зелёный
            anim1 = Animation(md_bg_color=(0.7, 1, 0.7, 1), d=0.2)
            # возвращаем к исходному
            anim2 = Animation(md_bg_color=orig_color, d=0.5)
            anim1 += anim2
            anim1.start(card)

    def open_menu(self):
        from kivy.app import App
        App.get_running_app().show_menu_popup()

    def open_history(self):
        self.manager.current = "history"

    def focus_barcode(self):
        if "barcode_input" in self.ids:
            self.ids.barcode_input.focus = True

    def process_barcode(self, code):
        code = code.strip()
        if not code:
            return
        order = getattr(AppSession, "order", None)
        stage = getattr(AppSession, "stage", None)
        user = getattr(AppSession, "user", None)
        if not order:
            self.show_status("Сначала выберите заказ!", error=True)
            return
        if not stage:
            self.show_status("Сначала выберите этап!", error=True)
            return
        if not user:
            self.show_status("Нет пользователя", error=True)
            return

        repo = Repository()

        barcode_data = dict(
            code=code,
            order=order.id,
            user_id=user.id,
            stage=stage.id,
            is_good=self.is_good_state,
            created_at=datetime.now(),
            is_sent=False,
            error_count=0
        )

        result = repo.save_and_send_barcode(barcode_data)
        if not result["success"]:
            if result.get("reason") == "duplicate":
                self.show_status("Такой штрихкод уже есть для этого этапа!", error=True)
            elif result.get("reason") == "db_error":
                self.show_status(f"Ошибка БД: {result.get('error')}", error=True)
            else:
                self.show_status("Ошибка отправки", error=True)
            self.ids.barcode_input.text = ""
            self.ids.barcode_input.focus = True
            return
        self.show_status("Отправлено", success=True)
        self.ids.barcode_input.text = ""
        self.ids.barcode_input.focus = True

    def show_status(self, msg, success=False, error=False):
        self.ids.save_status.text = msg
        if success:
            self.status_color = [0, 0.6, 0.2, 1]
        elif error:
            self.status_color = [1, 0.2, 0.2, 1]
        else:
            self.status_color = [0.1, 0.5, 0.2, 1]

    def on_barcode_text(self, text):
        if len(text.strip()) >= 12:
            self.process_barcode(text)

    def is_repair_stage(self):
        stage = getattr(AppSession, "stage", None)
        if stage and hasattr(stage, "name"):
            return "ремонт" in stage.name.lower()
        return False

    def update_state_button(self):
        if hasattr(self, 'ids') and 'state_btn' in self.ids:
            is_repair = self.is_repair_stage()
            self.ids.state_btn.disabled = not is_repair
            # Обновляем цвет текста в зависимости от состояния
            self.ids.state_btn.text_color = (0, 0.7, 0, 1) if self.is_good_state else (1, 0.2, 0.2, 1)

    def open_state_popup(self):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup
        layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        btn_good = Button(text="Is Good", background_color=(0.6, 1, 0.6, 1), size_hint_y=None, height=48)
        btn_defect = Button(text="Is Defect", background_color=(1, 0.5, 0.5, 1), size_hint_y=None, height=48)
        layout.add_widget(btn_good)
        layout.add_widget(btn_defect)
        popup = Popup(title="Выберите состояние", content=layout, size_hint=(0.5, 0.4))

        def update_state(state):
            self.is_good_state = state
            self.update_state_button()
            popup.dismiss()
            Clock.schedule_once(lambda dt: self.focus_barcode(), 0.2)

        btn_good.bind(on_release=lambda x: update_state(True))
        btn_defect.bind(on_release=lambda x: update_state(False))
        popup.open()

