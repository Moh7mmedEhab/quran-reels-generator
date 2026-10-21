from flask import Flask
from config import Config

def create_app(config_object=Config):
    app=Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_object)
    from .routes import bp
    app.register_blueprint(bp)
    return app
