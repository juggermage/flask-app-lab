"""Сховище товарів на основі TinyDB (JSON-файл data/products.json)."""

from datetime import datetime

from flask import current_app
from tinydb import TinyDB
from tinydb.table import Document

TABLE_NAME = "products"


def _open(path=None):
    path = path or current_app.config["PRODUCTS_DB_PATH"]
    return TinyDB(path, create_dirs=True, encoding="utf-8", indent=2, ensure_ascii=False)


def init_storage(app):
    """Створює файл бази й таблицю товарів, якщо їх ще немає."""
    with _open(app.config["PRODUCTS_DB_PATH"]) as db:
        if TABLE_NAME not in db.tables():
            db.storage.write({**(db.storage.read() or {}), TABLE_NAME: {}})


def all_products():
    with _open() as db:
        items = [dict(doc) for doc in db.table(TABLE_NAME).all()]
    return sorted(items, key=lambda p: p["id"])


def get_product(product_id):
    with _open() as db:
        doc = db.table(TABLE_NAME).get(doc_id=product_id)
    return dict(doc) if doc is not None else None


def add_product(data):
    """Додає товар: id та created_at виставляються автоматично."""
    with _open() as db:
        table = db.table(TABLE_NAME)
        new_id = max((doc.doc_id for doc in table.all()), default=0) + 1
        product = {
            "id": new_id,
            **data,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        table.insert(Document(product, doc_id=new_id))
    return product


def update_product(product_id, data):
    """Оновлює поля товару (id та created_at не змінюються). True, якщо товар існує."""
    data = {k: v for k, v in data.items() if k not in ("id", "created_at")}
    with _open() as db:
        table = db.table(TABLE_NAME)
        if not table.contains(doc_id=product_id):
            return False
        table.update(data, doc_ids=[product_id])
    return True


def delete_product(product_id):
    """Видаляє товар. Повертає видалений запис або None."""
    with _open() as db:
        table = db.table(TABLE_NAME)
        doc = table.get(doc_id=product_id)
        if doc is None:
            return None
        table.remove(doc_ids=[product_id])
    return dict(doc)
