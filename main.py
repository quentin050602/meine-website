from flask import Flask, render_template
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from threading import Thread

# Flask App
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Willkommen bei der Fitness-App!"

# Kivy App
class FitnessWidget(Widget):
    pass

class FitnessApp(App):
    def build(self):
        Window.size = (375, 812)  # iPhone-Screen-Größe simulieren
        return FitnessWidget()

    def start_flask(self):
        # Starte Flask in einem separaten Thread
        def run_flask():
            flask_app.run(host='0.0.0.0', port=5000)
        thread = Thread(target=run_flask)
        thread.daemon = True
        thread.start()

    def on_start(self):
        # Starte den Flask-Server, wenn die App startet
        self.start_flask()

if __name__ == '__main__':
    FitnessApp().run()


 

