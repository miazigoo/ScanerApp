import sys

from kivy.storage.jsonstore import JsonStore
import os

from kivymd.icon_definitions import md_icons
from kivy.lang import Builder
from kivymd.uix.toolbar import MDTopAppBar

from data.db import engine
from models.models import Base
from data.session import AppSession
from viewmodels.barcode_list_vm import BarcodeListScreen

from viewmodels.login_vm import LoginScreen   # login.py
from viewmodels.main_vm import MainScreen     # main_vm.py (MainScreen)

from kivymd.uix.screenmanager import MDScreenManager
from kivymd.app import MDApp

from viewmodels.order_select_vm import OrderSelectScreen
from viewmodels.settings_vm import SettingsScreen
from kivy.utils import platform

Base.metadata.create_all(engine)

def resource_path(rel_path):
    if platform == 'android':
        from kivy.resources import resource_find
        return resource_find(rel_path) or rel_path
    elif hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)

class MyApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = AppSession()
        self.menu_popup = None

        # Простое определение директории настроек
        if platform == 'android':
            # Используем внутреннее хранилище приложения
            settings_dir = '/data/data/argos.net.barcodescanner/files'
        else:
            settings_dir = self.user_data_dir

        # Создаем директорию если не существует
        os.makedirs(settings_dir, exist_ok=True)

        self.settings_path = os.path.join(settings_dir, "app_settings.json")
        self.theme_store = JsonStore(self.settings_path)

    def build(self):
        self.apply_saved_theme()
        kv_files = [
            "screens/login.kv",
            "screens/menu_popup.kv",
            "screens/settings.kv",
            "screens/main.kv",
            "screens/barcode_list.kv",
            "screens/order_select.kv"
        ]

        for kv_file in kv_files:
            kv_path = resource_path(kv_file)
            if os.path.exists(kv_path) or platform == 'android':
                try:
                    Builder.load_file(kv_path)
                except Exception as e:
                    print(f"Error loading {kv_file}: {e}")

        sm = MDScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(BarcodeListScreen(name="history"))
        sm.add_widget(OrderSelectScreen(name="order_select"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

    def show_menu_popup(self):
        from kivy.lang import Builder
        from kivymd.uix.dialog import MDDialog

        if not self.menu_popup:
            # Загружаем контент из kv
            content = Builder.load_string(
                '''
MenuPopup:
                '''
            )
            self.menu_popup = MDDialog(
                type="custom",
                content_cls=content,
                auto_dismiss=True,
                background_color=(1, 0.85, 0.7, 1),
                radius=[16, 16, 16, 16]
            )
        self.menu_popup.open()

    def dismiss_menu_popup(self, *args):
        if self.menu_popup:
            self.menu_popup.dismiss()

    def show_history(self):
        self.root.current = "history"

    def show_settings(self):
        self.root.current = "settings"

    def logout(self):
        self.root.current = "login"

    def show_main(self):
        self.root.current = "main"

    def apply_saved_theme(self):
        try:
            if self.theme_store.exists("theme"):
                theme = self.theme_store.get("theme")
                self.theme_cls.theme_style = theme.get("theme_style", "Light")
                self.theme_cls.primary_palette = theme.get("primary_palette", "Blue")
                self.current_custom_theme = theme.get("current_custom_theme", "Light")
        except Exception as e:
            print(f"Error loading theme: {e}")
            # Устанавливаем тему по умолчанию
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"

    def save_theme_settings(self):
        try:
            self.theme_store.put(
                "theme",
                theme_style=self.theme_cls.theme_style,
                primary_palette=self.theme_cls.primary_palette,
                current_custom_theme=getattr(self, "current_custom_theme", "Light")
            )
        except Exception as e:
            print(f"Error saving theme: {e}")


if __name__ == "__main__":
    # Создание и запуск приложения
    MyApp().run()