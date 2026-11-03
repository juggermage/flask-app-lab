"""Конфігурація застосунку. Підключається через app.config.from_pyfile("../config.py")."""

import os

# Коренева папка проєкту (там, де лежить цей файл)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "lab3-dev-secret-key"
DEBUG = True

# Лабораторна 5: контактна форма
CONTACT_LOG_PATH = os.path.join(BASE_DIR, "logs", "contact.log")

# Лабораторна 5: товари (TinyDB) та завантажені зображення
PRODUCTS_DB_PATH = os.path.join(BASE_DIR, "data", "products.json")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "products", "static", "uploads")
MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # жорстка межа розміру запиту (8 МБ)
