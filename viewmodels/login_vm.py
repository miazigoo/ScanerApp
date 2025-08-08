from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from data.repository import Repository
from data.session import AppSession


class LoginScreen(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    token = ObjectProperty(None)
    error_label = ObjectProperty(None)
    scheduled_token_login = None

    def on_pre_enter(self, *args):
        # По умолчанию режим логин/пароль
        self.set_mode("Логин/Пароль")
        # Автофокус на поле логина при входе на экран
        Clock.schedule_once(lambda dt: self.ids.username.focus == True, 0.1)

    def set_mode(self, mode):
        if mode == "Логин/Пароль":
            self.ids.login_fields.opacity = 1
            self.ids.login_fields.disabled = False
            self.ids.login_button_box.opacity = 1
            self.ids.login_button_box.disabled = False

            self.ids.token_fields.opacity = 0
            self.ids.token_fields.disabled = True
            self.ids.token_button_box.opacity = 0
            self.ids.token_button_box.disabled = True

            # Автофокус на поле логина
            Clock.schedule_once(lambda dt: setattr(self.ids.username, 'focus', True), 0.1)
        else:
            self.ids.login_fields.opacity = 0
            self.ids.login_fields.disabled = True
            self.ids.login_button_box.opacity = 0
            self.ids.login_button_box.disabled = True

            self.ids.token_fields.opacity = 1
            self.ids.token_fields.disabled = False
            self.ids.token_button_box.opacity = 1
            self.ids.token_button_box.disabled = False

            # Автофокус на поле токена
            Clock.schedule_once(lambda dt: setattr(self.ids.token, 'focus', True), 0.1)

    def login(self):
        username = self.ids.username.text.strip()
        password = self.ids.password.text

        repo = Repository()
        try:
            user = repo.api.login(username, password)
            AppSession.user = user
            AppSession.permissions = getattr(user, "permissions", [])

            main_screen = self.manager.get_screen("main")
            if hasattr(main_screen, "on_pre_enter"):
                main_screen.on_pre_enter()
            # Переход на main
            self.manager.current = "main"   # Переход на главный экран
        except Exception as e:
            self.ids.error_label.text = f"Ошибка: {e}"

    def login_token(self):
        token = self.ids.token.text.strip()
        # Здесь реализуйте свою логику входа по токену (например, repo.api.login_by_token(token))
        if not token:
            self.ids.error_label.text = "Введите токен!"
            return
        try:
            user = Repository().api.login_by_token(token)
            AppSession.user = user
            AppSession.permissions = getattr(user, "permissions", [])
            main_screen = self.manager.get_screen("main")
            if hasattr(main_screen, "on_pre_enter"):
                main_screen.on_pre_enter()
            self.manager.current = "main"
        except Exception as e:
            self.ids.error_label.text = f"Ошибка: {e}"

    def on_token_text(self, text):
        if self.scheduled_token_login:
            self.scheduled_token_login.cancel()
            self.scheduled_token_login = None
        if len(text.strip()) >= 10:
            self.scheduled_token_login = Clock.schedule_once(lambda dt: self.login_token(), 0.2)
