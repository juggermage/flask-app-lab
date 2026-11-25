import os

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from .config import config
from .models import Base

# Розширення створюються без застосунку і прив'язуються до нього у create_app()
db = SQLAlchemy(model_class=Base)
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message = "Спочатку увійдіть у систему."
login_manager.login_message_category = "warning"


def create_app(config_name=None):
    """Application factory: створює застосунок для вказаного режиму.

    config_name: "development" | "testing" | "production".
    Якщо не задано — береться зі змінної середовища FLASK_CONFIG (за замовчуванням development).
    """
    config_name = config_name or os.getenv("FLASK_CONFIG", "default")
    config_class = config[config_name]

    app = Flask(__name__)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Розширення
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)  # batch-режим потрібен SQLite для ALTER

    # Головні сторінки (/, /resume, /contacts, ...)
    from .views import register_views

    register_views(app)

    # Блюпринти
    from .users import user_bp
    from .products import product_bp
    from .posts import post_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(post_bp)

    # Сховище товарів (TinyDB) з лабораторної 5
    from .products.storage import init_storage

    init_storage(app)

    from .seed import register_commands

    register_commands(app)

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html", title="Не знайдено"), 404

    return app
