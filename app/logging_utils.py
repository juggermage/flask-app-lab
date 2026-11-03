"""Запис даних контактної форми у log-файл (модуль logging)."""

import json
import logging
import os

_logger = logging.getLogger("contact_form")
_logger.setLevel(logging.INFO)
_logger.propagate = False


def get_contact_logger(path):
    """Повертає логер, що пише у файл `path` (створює папку й handler за потреби)."""
    path = os.path.abspath(path)
    for handler in list(_logger.handlers):
        if getattr(handler, "baseFilename", None) == path:
            return _logger
        _logger.removeHandler(handler)  # змінився шлях -> перестворюємо handler
        handler.close()

    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _logger.addHandler(handler)
    return _logger


def log_contact(path, data):
    """Дописує одну рядок-запис у лог. Кидає OSError, якщо файл недоступний."""
    logger = get_contact_logger(path)
    logger.info(json.dumps(data, ensure_ascii=False))
    for handler in logger.handlers:
        handler.flush()
