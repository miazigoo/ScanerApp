# stage_button.py
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.behaviors import HoverBehavior
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.app import App


class StageButton(HoverBehavior, MDRaisedButton):
    normal_height = 28
    hover_height = 34

    def __init__(self, **kwargs):
        kwargs.setdefault('size_hint', (1, None))  # Растягиваем по ширине
        kwargs.setdefault('height', self.normal_height)
        super().__init__(**kwargs)
        self.md_bg_color = self.get_bg_normal()

    def get_bg_normal(self):
        app = App.get_running_app()
        # Можно выбрать любой подходящий цвет из theme_cls
        if app.theme_cls.theme_style == "Light":
            return app.theme_cls.primary_color  # стандартный светлый фон
        else:
            return app.theme_cls.primary_color   # стандартный тёмный фон

    def get_bg_hover(self):
        app = App.get_running_app()
        if app.theme_cls.theme_style == "Light":
            return [0.8, 0.95, 1, 1]  # нежно-голубой
        else:
            return [0.2, 0.3, 0.5, 1]  # тёмно-синий

    def on_enter(self, *args):
        Animation(md_bg_color=self.get_bg_hover(), height=self.hover_height, d=0.12).start(self)
    def on_leave(self, *args):
        Animation(md_bg_color=self.get_bg_normal(), height=self.normal_height, d=0.12).start(self)
