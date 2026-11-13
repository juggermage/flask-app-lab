import unittest

from app import create_app  # переконуємось, що імпортовано Flask-додаток


class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        """Налаштування клієнта тестування перед кожним тестом."""
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_greetings_page(self):
        """Тест маршруту /users/hi/<name>."""
        response = self.client.get("/users/hi/John?age=30")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"JOHN", response.data)
        self.assertIn(b"30", response.data)

    def test_greetings_without_age(self):
        """Без параметра age сторінка показує, що вік не вказано."""
        response = self.client.get("/users/hi/John")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"JOHN", response.data)
        self.assertIn(b"Not provided", response.data)

    def test_admin_page(self):
        """Тест маршруту /users/admin, який перенаправляє."""
        response = self.client.get("/users/admin", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ADMINISTRATOR", response.data)
        self.assertIn(b"45", response.data)

    def test_admin_redirect_status(self):
        """/users/admin без follow_redirects повертає 302 на greetings."""
        response = self.client.get("/users/admin")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/hi/administrator", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
