"""Конфігурація застосунку. Підключається через app.config.from_pyfile("../config.py")."""

import os

# Коренева папка проєкту (там, де лежить цей файл)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "lab3-dev-secret-key"
DEBUG = True

# Лабораторна 5: контактна форма
CONTACT_LOG_PATH = os.path.join(BASE_DIR, "logs", "contact.log")
