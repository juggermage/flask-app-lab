"""Конфігурація застосунку за режимами: development, testing, production."""

import os
import tempfile

from dotenv import load_dotenv

# Коренева папка проєкту (на рівень вище за папку app/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# Підвантажуємо змінні з .env (для `python run.py`; `flask ...` робить це сам)
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    """Базова конфігурація для всіх середовищ."""

    SECRET_KEY = os.getenv("SECRET_KEY", "lab6-dev-secret-key")
    DEBUG = False
    TESTING = False

    # SQLAlchemy: відносний шлях sqlite:///data.sqlite -> instance/data.sqlite
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///data.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Лабораторна 5: контактна форма
    CONTACT_LOG_PATH = os.path.join(BASE_DIR, "logs", "contact.log")

    # Лабораторна 5: товари (TinyDB) та завантажені зображення
    PRODUCTS_DB_PATH = os.path.join(BASE_DIR, "data", "products.json")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "products", "static", "uploads")
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # жорстка межа розміру запиту (8 МБ)

    @staticmethod
    def init_app(app):
        """Хук для додаткової ініціалізації, специфічної для середовища."""


class DevelopmentConfig(Config):
    """Режим розробки (використовується за замовчуванням)."""

    DEBUG = True


class TestingConfig(Config):
    """Тести: in-memory SQLite, вимкнений CSRF, тимчасові файли замість реальних."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

    _TMP = os.path.join(tempfile.gettempdir(), "flask_app_lab6_tests")
    CONTACT_LOG_PATH = os.path.join(_TMP, "logs", "contact.log")
    PRODUCTS_DB_PATH = os.path.join(_TMP, "data", "products.json")
    UPLOAD_FOLDER = os.path.join(_TMP, "uploads")


class ProductionConfig(Config):
    """Продакшен: без DEBUG, захищені cookie, обов'язковий SECRET_KEY зі середовища."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    @classmethod
    def init_app(cls, app):
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("У production потрібно задати змінну середовища SECRET_KEY.")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
