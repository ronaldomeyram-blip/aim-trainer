from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from math import sin, hypot
import random


# ---------------------------------------------------------
# MENU SCREEN
# ---------------------------------------------------------
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.t = 0
        self.root_widget = FloatLayout()

        # --- Vong tron FOV trang tri phia sau menu ---
        with self.root_widget.canvas.before:
            self.circle_color = Color(0, 1, 0, 0.6)
            self.fov_circle = Line(circle=(0, 0, 140), width=2)

            self.circle_color2 = Color(0, 1, 1, 0.3)
            self.fov_circle2 = Line(circle=(0, 0, 180), width=1.5)

        Clock.schedule_interval(self.update_circle, 1 / 30)

        layout = BoxLayout(orientation="vertical", padding=60, spacing=20)

        title = Label(text="AIM TRAINER", font_size=48, size_hint=(1, 0.4))
        layout.add_widget(title)

        btn_start = Button(text="Bat dau (Start)", font_size=24, size_hint=(1, 0.15))
        btn_start.bind(on_release=self.go_to_game)
        layout.add_widget(btn_start)

        btn_settings = Button(text="Cai dat (Settings)", font_size=24, size_hint=(1, 0.15))
        btn_settings.bind(on_release=self.go_to_settings)
        layout.add_widget(btn_settings)

        btn_quit = Button(text="Thoat (Quit)", font_size=24, size_hint=(1, 0.15))
        btn_quit.bind(on_release=self.quit_app)
        layout.add_widget(btn_quit)

        self.root_widget.add_widget(layout)
        self.add_widget(self.root_widget)

    def update_circle(self, dt):
        cx = self.root_widget.width / 2
        cy = self.root_widget.height / 2

        # Vong tron pulsing ban kinh nhe theo thoi gian
        pulse = 10 * sin(self.t)
        self.fov_circle.circle = (cx, cy, 140 + pulse)
        self.fov_circle2.circle = (cx, cy, 180 + pulse)

        self.t += dt * 2

    def go_to_game(self, *args):
        self.manager.current = "game"

    def go_to_settings(self, *args):
        self.manager.current = "settings"

    def quit_app(self, *args):
        App.get_running_app().stop()
        Window.close()


# ---------------------------------------------------------
# SETTINGS SCREEN
# ---------------------------------------------------------
class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical", padding=60, spacing=20)

        title = Label(text="Cai dat", font_size=36, size_hint=(1, 0.2))
        self.layout.add_widget(title)

        # Target size slider
        self.size_label = Label(text="Kich thuoc target: 25", font_size=20, size_hint=(1, 0.1))
        self.layout.add_widget(self.size_label)

        self.size_slider = Slider(min=10, max=60, value=25, size_hint=(1, 0.15))
        self.size_slider.bind(value=self.on_size_change)
        self.layout.add_widget(self.size_slider)

        # Game duration slider
        self.time_label = Label(text="Thoi gian choi: 30s", font_size=20, size_hint=(1, 0.1))
        self.layout.add_widget(self.time_label)

        self.time_slider = Slider(min=10, max=120, value=30, size_hint=(1, 0.15))
        self.time_slider.bind(value=self.on_time_change)
        self.layout.add_widget(self.time_slider)

        btn_back = Button(text="Quay lai (Back)", font_size=22, size_hint=(1, 0.15))
        btn_back.bind(on_release=self.go_back)
        self.layout.add_widget(btn_back)

        self.add_widget(self.layout)

    def on_size_change(self, instance, value):
        self.size_label.text = f"Kich thuoc target: {int(value)}"

    def on_time_change(self, instance, value):
        self.time_label.text = f"Thoi gian choi: {int(value)}s"

    def go_back(self, *args):
        self.manager.current = "menu"


# ---------------------------------------------------------
# GAME SCREEN (the aim trainer itself)
# ---------------------------------------------------------
class AimTrainerWidget(FloatLayout):
    def __init__(self, get_settings, on_game_over, **kwargs):
        super().__init__(**kwargs)
        self.get_settings = get_settings   # callable -> (target_radius, duration)
        self.on_game_over = on_game_over   # callback(score, misses)

        self.radius = 150
        self.t = 0

        self.score = 0
        self.misses = 0
        self.time_left = 30
        self.target_radius = 25

        self.target_x = 0
        self.target_y = 0

        self.running = False
        self.paused = False
        self._update_event = None

        # --- HUD ---
        self.score_label = Label(
            text="Score: 0  |  Misses: 0",
            size_hint=(None, None),
            size=(300, 40),
            pos_hint={"x": 0, "top": 1},
            font_size=20,
        )
        self.add_widget(self.score_label)

        self.timer_label = Label(
            text="Time: 30",
            size_hint=(None, None),
            size=(200, 40),
            pos_hint={"right": 1, "top": 1},
            font_size=20,
        )
        self.add_widget(self.timer_label)

        # --- Graphics (created once, updated each frame) ---
        with self.canvas:
            Color(0, 1, 0)
            self.fov_circle = Line(circle=(0, 0, self.radius), width=2)

            Color(1, 1, 1)
            self.crosshair_h = Line(points=[0, 0, 0, 0], width=2)
            self.crosshair_v = Line(points=[0, 0, 0, 0], width=2)

            self.frame_color = Color(1, 0, 0)
            self.rgb_frame = Line(rectangle=(20, 0, 300, 150), width=3)

            self.target_color = Color(1, 0.2, 0.2)
            self.target = Ellipse(pos=(0, 0), size=(50, 50))
            Color(0, 0, 0)
            self.target_outline = Line(circle=(0, 0, 25), width=2)

    def start_game(self):
        self.target_radius, self.time_left = self.get_settings()
        self.score = 0
        self.misses = 0
        self.running = True
        self.score_label.text = "Score: 0  |  Misses: 0"
        self.timer_label.text = f"Time: {int(self.time_left)}"
        self.spawn_target()

        if self._update_event:
            self._update_event.cancel()
        self._update_event = Clock.schedule_interval(self.update, 1 / 60)

    def stop_game(self):
        self.running = False
        self.paused = False
        if self._update_event:
            self._update_event.cancel()
            self._update_event = None

    def pause_game(self):
        self.paused = True

    def resume_game(self):
        self.paused = False

    def spawn_target(self):
        margin = self.target_radius + 10
        if self.width > 2 * margin and self.height > 2 * margin:
            self.target_x = random.uniform(margin, self.width - margin)
            self.target_y = random.uniform(margin, self.height - margin)
        else:
            self.target_x = self.width / 2
            self.target_y = self.height / 2

    def update(self, dt):
        if not self.running or self.paused:
            return

        cx = self.width / 2
        cy = self.height / 2

        self.fov_circle.circle = (cx, cy, self.radius)
        self.crosshair_h.points = [cx - 15, cy, cx + 15, cy]
        self.crosshair_v.points = [cx, cy - 15, cx, cy + 15]

        r = (sin(self.t) + 1) / 2
        g = (sin(self.t + 2) + 1) / 2
        b = (sin(self.t + 4) + 1) / 2
        self.frame_color.rgb = (r, g, b)
        self.rgb_frame.rectangle = (20, self.height - 180, 300, 150)

        self.target.size = (self.target_radius * 2, self.target_radius * 2)
        self.target.pos = (self.target_x - self.target_radius, self.target_y - self.target_radius)
        self.target_outline.circle = (self.target_x, self.target_y, self.target_radius)

        self.t += dt * 2

        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.timer_label.text = "Time: 0"
            self.stop_game()
            self.on_game_over(self.score, self.misses)
        else:
            self.timer_label.text = f"Time: {int(self.time_left)}"

    def on_touch_down(self, touch):
        if not self.running or self.paused:
            return super().on_touch_down(touch)

        dist = hypot(touch.x - self.target_x, touch.y - self.target_y)
        if dist <= self.target_radius:
            self.score += 1
            self.spawn_target()
        else:
            self.misses += 1
        self.score_label.text = f"Score: {self.score}  |  Misses: {self.misses}"
        return super().on_touch_down(touch)


# ---------------------------------------------------------
# PAUSE OVERLAY (hien thi de len tren game khi tam dung)
# ---------------------------------------------------------
class PauseOverlay(FloatLayout):
    def __init__(self, on_resume, on_restart, on_menu, **kwargs):
        super().__init__(**kwargs)
        self.t = 0

        # Nen mo den phia sau + vong tron trang tri pulsing
        with self.canvas.before:
            Color(0, 0, 0, 0.75)
            self.bg = Rectangle(pos=(0, 0), size=(0, 0))

            self.circle_color1 = Color(0, 1, 0, 0.6)
            self.deco_circle1 = Line(circle=(0, 0, 120), width=2)

            self.circle_color2 = Color(0, 1, 1, 0.35)
            self.deco_circle2 = Line(circle=(0, 0, 160), width=1.5)

        self.bind(size=self.update_bg, pos=self.update_bg)
        Clock.schedule_interval(self.update_circle, 1 / 30)

        box = BoxLayout(orientation="vertical", padding=60, spacing=20,
                         size_hint=(0.8, 0.6), pos_hint={"center_x": 0.5, "center_y": 0.5})

        title = Label(text="TAM DUNG", font_size=36, size_hint=(1, 0.3))
        box.add_widget(title)

        btn_resume = Button(text="Tiep tuc", font_size=22, size_hint=(1, 0.2))
        btn_resume.bind(on_release=lambda *a: on_resume())
        box.add_widget(btn_resume)

        btn_restart = Button(text="Choi lai", font_size=22, size_hint=(1, 0.2))
        btn_restart.bind(on_release=lambda *a: on_restart())
        box.add_widget(btn_restart)

        btn_menu = Button(text="Ve menu chinh", font_size=22, size_hint=(1, 0.2))
        btn_menu.bind(on_release=lambda *a: on_menu())
        box.add_widget(btn_menu)

        self.add_widget(box)

    def update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

    def update_circle(self, dt):
        cx = self.width / 2
        cy = self.height / 2
        pulse = 8 * sin(self.t)
        self.deco_circle1.circle = (cx, cy, 120 + pulse)
        self.deco_circle2.circle = (cx, cy, 160 + pulse)
        self.t += dt * 2


class GameScreen(Screen):
    def __init__(self, settings_screen, **kwargs):
        super().__init__(**kwargs)
        self.settings_screen = settings_screen
        self.pause_overlay = None

        self.root_layout = FloatLayout()
        self.trainer = AimTrainerWidget(
            get_settings=self.get_settings,
            on_game_over=self.game_over,
        )
        self.root_layout.add_widget(self.trainer)

        # Nut tam dung (thay cho nut thoat truoc day)
        btn_pause = Button(
            text="II",
            size_hint=(None, None),
            size=(50, 50),
            pos_hint={"right": 1, "top": 1},
        )
        btn_pause.bind(on_release=self.show_pause)
        self.root_layout.add_widget(btn_pause)

        self.add_widget(self.root_layout)

    def get_settings(self):
        radius = int(self.settings_screen.size_slider.value)
        duration = int(self.settings_screen.time_slider.value)
        return radius, duration

    def on_enter(self, *args):
        self.trainer.start_game()

    def show_pause(self, *args):
        if self.pause_overlay is not None:
            return  # da dang mo roi
        self.trainer.pause_game()
        self.pause_overlay = PauseOverlay(
            on_resume=self.hide_pause,
            on_restart=self.restart_game,
            on_menu=self.exit_to_menu,
        )
        self.root_layout.add_widget(self.pause_overlay)

    def hide_pause(self, *args):
        if self.pause_overlay is not None:
            self.root_layout.remove_widget(self.pause_overlay)
            self.pause_overlay = None
        self.trainer.resume_game()

    def restart_game(self, *args):
        self.hide_pause()
        self.trainer.start_game()

    def on_leave(self, *args):
        self.hide_pause()
        self.trainer.stop_game()

    def exit_to_menu(self, *args):
        self.manager.current = "menu"

    def game_over(self, score, misses):
        # Quay lai menu sau khi het gio, co the mo rong thanh man hinh ket qua rieng
        self.manager.current = "menu"


# ---------------------------------------------------------
# APP
# ---------------------------------------------------------
class AimTrainerApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition())

        menu_screen = MenuScreen(name="menu")
        settings_screen = SettingsScreen(name="settings")
        game_screen = GameScreen(settings_screen, name="game")

        sm.add_widget(menu_screen)
        sm.add_widget(settings_screen)
        sm.add_widget(game_screen)

        sm.current = "menu"
        return sm


if __name__ == "__main__":
    AimTrainerApp().run()
