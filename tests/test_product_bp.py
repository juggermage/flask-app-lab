import unittest

from flask import url_for

from app import app
from app.products.views import products


class ProductBlueprintTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_product_list_page(self):
        """/products/ повертає 200 і показує всі товари."""
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)
        for product in products:
            self.assertIn(product["name"].encode("utf-8"), response.data)
            self.assertIn(str(product["price"]).encode("utf-8"), response.data)

    def test_product_list_has_links_to_details(self):
        """У списку є посилання на сторінку кожного товару."""
        response = self.client.get("/products/")
        for product in products:
            link = f"/products/{product['id']}".encode("utf-8")
            self.assertIn(link, response.data)

    def test_product_detail_page(self):
        """/products/1 показує детальну інформацію про Laptop."""
        response = self.client.get("/products/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Laptop", response.data)
        self.assertIn(b"1200", response.data)
        self.assertIn("Intel Core i7".encode("utf-8"), response.data)

    def test_each_product_detail(self):
        """Кожен товар з масиву має робочу сторінку деталей."""
        for product in products:
            with self.subTest(product=product["name"]):
                response = self.client.get(f"/products/{product['id']}")
                self.assertEqual(response.status_code, 200)
                self.assertIn(product["name"].encode("utf-8"), response.data)

    def test_product_not_found(self):
        """Неіснуючий id -> 404."""
        response = self.client.get("/products/999")
        self.assertEqual(response.status_code, 404)

    def test_product_id_must_be_int(self):
        """Нечисловий id не підходить під <int:product_id> -> 404."""
        response = self.client.get("/products/abc")
        self.assertEqual(response.status_code, 404)

    def test_url_for_builds_prefixed_urls(self):
        """url_for будує адреси з префіксом блюпринта."""
        with app.test_request_context():
            self.assertEqual(url_for("products.product_list"), "/products/")
            self.assertEqual(url_for("products.product_detail", product_id=2), "/products/2")


if __name__ == "__main__":
    unittest.main()
