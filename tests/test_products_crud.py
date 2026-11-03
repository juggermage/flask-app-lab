import io
import json
import os
import tempfile
import unittest

from app import app
from app.products import storage

# мінімальний валідний PNG 1x1
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x9a\xa0\xa0"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class ProductCrudTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "data", "products.json")
        self.upload_dir = os.path.join(self.tmp.name, "uploads")
        keys = ("PRODUCTS_DB_PATH", "UPLOAD_FOLDER", "WTF_CSRF_ENABLED")
        self._saved = {k: app.config.get(k) for k in keys}
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            PRODUCTS_DB_PATH=self.db_path,
            UPLOAD_FOLDER=self.upload_dir,
        )
        self.client = app.test_client()

    def tearDown(self):
        app.config.update(self._saved)
        self.tmp.cleanup()

    # ---------- допоміжні методи ----------

    @staticmethod
    def product_data(**overrides):
        data = {
            "name": "Laptop",
            "content": "Потужний ноутбук для роботи.",
            "price": "1200.50",
            "category": "computers",
            "quantity": "5",
        }
        data.update(overrides)
        return data

    def add(self, image=None, **overrides):
        data = self.product_data(**overrides)
        if image is not None:
            data["image"] = image
        return self.client.post(
            "/product/add", data=data, content_type="multipart/form-data"
        )

    def png(self, name="photo.png"):
        return (io.BytesIO(PNG_BYTES), name)

    def uploads(self):
        return os.listdir(self.upload_dir) if os.path.isdir(self.upload_dir) else []

    # ---------- storage ----------

    def test_init_storage_creates_file_and_table(self):
        storage.init_storage(app)
        with open(self.db_path, encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"products": {}})

    def test_ids_are_unique_and_increasing(self):
        self.add(name="First")
        self.add(name="Second")
        with app.app_context():
            ids = [p["id"] for p in storage.all_products()]
        self.assertEqual(ids, [1, 2])

    # ---------- Create ----------

    def test_add_page_get(self):
        response = self.client.get("/product/add")
        self.assertEqual(response.status_code, 200)
        for field in ("name", "content", "price", "category", "quantity", "image"):
            self.assertIn(f'name="{field}"'.encode(), response.data)

    def test_add_product_prg_flash_and_persisted(self):
        response = self.add()
        self.assertEqual(response.status_code, 302)  # Post/Redirect/Get
        self.assertTrue(response.headers["Location"].endswith("/product/1"))

        page = self.client.get(response.headers["Location"])
        self.assertIn("успішно додано".encode(), page.data)
        self.assertIn(b"alert-success", page.data)
        self.assertIn(b"Laptop", page.data)
        self.assertIn(b"1200.50", page.data)

        with open(self.db_path, encoding="utf-8") as f:
            raw = json.load(f)["products"]["1"]
        self.assertEqual(raw["id"], 1)
        self.assertEqual(raw["price"], 1200.5)
        self.assertEqual(raw["quantity"], 5)
        self.assertEqual(raw["category"], "computers")
        self.assertIsNone(raw["image"])
        self.assertRegex(raw["created_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

    def test_add_validation_errors(self):
        cases = {
            "short name": ({"name": "ab"}, "від 3 до 100"),
            "empty content": ({"content": "  "}, "Додайте опис"),
            "zero price": ({"price": "0"}, "додатною"),
            "negative price": ({"price": "-5"}, "додатною"),
            "three decimals": ({"price": "10.999"}, "двох знаків"),
            "not a number": ({"price": "abc"}, ""),
            "negative quantity": ({"quantity": "-1"}, "Кількість не може"),
            "fractional quantity": ({"quantity": "1.5"}, ""),
            "unknown category": ({"category": "weapons"}, ""),
        }
        for label, (override, text) in cases.items():
            with self.subTest(label):
                response = self.add(**override)
                self.assertEqual(response.status_code, 200)  # форма повернулась з помилками
                self.assertIn(b"alert-danger", response.data)
                if text:
                    self.assertIn(text.encode(), response.data)
        with app.app_context():
            self.assertEqual(storage.all_products(), [])

    def test_add_zero_quantity_is_allowed(self):
        self.assertEqual(self.add(quantity="0").status_code, 302)

    def test_add_with_valid_image(self):
        response = self.add(image=self.png("My Photo.PNG"))
        self.assertEqual(response.status_code, 302)
        files = self.uploads()
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0], r"^[0-9a-f]{32}\.png$")  # UUID-ім'я, не оригінальне
        with app.app_context():
            product = storage.get_product(1)
        self.assertEqual(product["image"], f"uploads/{files[0]}")

    def test_add_rejects_bad_extension(self):
        response = self.add(image=(io.BytesIO(b"hello"), "notes.txt"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Дозволені формати".encode(), response.data)
        self.assertEqual(self.uploads(), [])

    def test_add_rejects_too_large_image(self):
        big = (io.BytesIO(b"0" * (2 * 1024 * 1024 + 1)), "big.jpg")
        response = self.add(image=big)
        self.assertEqual(response.status_code, 200)
        self.assertIn("завеликий".encode(), response.data)
        self.assertEqual(self.uploads(), [])

    # ---------- Read ----------

    def test_list_empty(self):
        response = self.client.get("/product")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Товарів поки немає".encode(), response.data)

    def test_list_shows_product_fields_and_placeholder(self):
        self.add()
        response = self.client.get("/product")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn("Комп&#39;ютери".encode(), response.data)  # категорія
        self.assertIn(b"1200.50", response.data)
        self.assertIn("5 шт.".encode(), response.data)
        self.assertIn("Додано:".encode(), response.data)
        self.assertIn("Немає зображення".encode(), response.data)  # без картинки
        self.assertIn(b"/product/1", response.data)

    def test_list_shows_image_when_present(self):
        self.add(image=self.png())
        response = self.client.get("/product")
        self.assertIn(b"/product/static/uploads/", response.data)
        self.assertNotIn("Немає зображення".encode(), response.data)

    def test_list_handles_missing_image_file(self):
        self.add(image=self.png())
        for name in self.uploads():
            os.remove(os.path.join(self.upload_dir, name))
        response = self.client.get("/product")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Немає зображення".encode(), response.data)

    def test_detail_page(self):
        self.add()
        response = self.client.get("/product/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Потужний ноутбук".encode(), response.data)
        self.assertIn(b"/product/1/edit", response.data)
        self.assertIn(b"/product/1/delete", response.data)

    def test_detail_not_found(self):
        response = self.client.get("/product/999")
        self.assertEqual(response.status_code, 404)

    def test_detail_id_must_be_int(self):
        self.assertEqual(self.client.get("/product/abc").status_code, 404)

    # ---------- Update ----------

    def test_edit_page_prefilled(self):
        self.add()
        response = self.client.get("/product/1/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'value="Laptop"', response.data)
        self.assertIn(b'value="1200.50"', response.data)
        self.assertIn("Потужний ноутбук".encode(), response.data)

    def test_edit_updates_fields_keeps_id_and_created_at(self):
        self.add()
        with app.app_context():
            before = storage.get_product(1)
        response = self.client.post(
            "/product/1/edit",
            data=self.product_data(name="Laptop Pro", price="999.99", quantity="2"),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            after = storage.get_product(1)
        self.assertEqual(after["name"], "Laptop Pro")
        self.assertEqual(after["price"], 999.99)
        self.assertEqual(after["quantity"], 2)
        self.assertEqual(after["id"], before["id"])
        self.assertEqual(after["created_at"], before["created_at"])
        page = self.client.get(response.headers["Location"])
        self.assertIn("оновлено".encode(), page.data)

    def test_edit_keeps_old_image_when_no_new_file(self):
        self.add(image=self.png())
        old = self.uploads()
        self.client.post(
            "/product/1/edit", data=self.product_data(name="Renamed"),
            content_type="multipart/form-data",
        )
        with app.app_context():
            product = storage.get_product(1)
        self.assertEqual(product["image"], f"uploads/{old[0]}")
        self.assertEqual(self.uploads(), old)

    def test_edit_replaces_image_and_removes_old_file(self):
        self.add(image=self.png())
        old = self.uploads()[0]
        data = self.product_data()
        data["image"] = self.png("new.jpg")
        self.client.post("/product/1/edit", data=data, content_type="multipart/form-data")
        files = self.uploads()
        self.assertEqual(len(files), 1)
        self.assertNotEqual(files[0], old)
        self.assertTrue(files[0].endswith(".jpg"))

    def test_edit_validation_error_does_not_change_data(self):
        self.add()
        response = self.client.post(
            "/product/1/edit", data=self.product_data(name="x"),
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(storage.get_product(1)["name"], "Laptop")

    def test_edit_not_found(self):
        self.assertEqual(self.client.get("/product/42/edit").status_code, 404)
        r = self.client.post("/product/42/edit", data=self.product_data())
        self.assertEqual(r.status_code, 404)

    # ---------- Delete ----------

    def test_delete_requires_post(self):
        self.add()
        self.assertEqual(self.client.get("/product/1/delete").status_code, 405)

    def test_delete_removes_product_and_image(self):
        self.add(image=self.png())
        response = self.client.post("/product/1/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("видалено".encode(), response.data)
        with app.app_context():
            self.assertIsNone(storage.get_product(1))
        self.assertEqual(self.uploads(), [])
        self.assertEqual(self.client.get("/product/1").status_code, 404)

    def test_delete_not_found(self):
        self.assertEqual(self.client.post("/product/5/delete").status_code, 404)

    def test_delete_without_csrf_token_is_rejected(self):
        self.add()
        app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/product/1/delete", follow_redirects=True)
        self.assertIn("CSRF".encode(), response.data)
        with app.app_context():
            self.assertIsNotNone(storage.get_product(1))

    def test_ids_after_deleting_middle_item(self):
        for n in ("One", "Two", "Three"):
            self.add(name=n)
        self.client.post("/product/2/delete")
        self.add(name="Four")
        with app.app_context():
            ids = [p["id"] for p in storage.all_products()]
        self.assertEqual(ids, [1, 3, 4])

    # ---------- Persistence / CSRF ----------

    def test_data_persists_between_requests_and_reopen(self):
        self.add()
        with app.app_context():
            first = storage.all_products()
            second = storage.all_products()  # нове відкриття файлу
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)

    def test_add_csrf_protection(self):
        app.config["WTF_CSRF_ENABLED"] = True
        response = self.add()
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(storage.all_products(), [])


if __name__ == "__main__":
    unittest.main()
