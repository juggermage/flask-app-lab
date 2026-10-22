import unittest

from app import app


class MainViewsTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Flask Application", response.data)

    def test_homepage_shows_user_agent(self):
        response = self.client.get("/homepage", headers={"User-Agent": "TestAgent/1.0"})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"TestAgent/1.0", response.data)

    def test_resume_page(self):
        response = self.client.get("/resume")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Освіта".encode("utf-8"), response.data)

    def test_contacts_get(self):
        response = self.client.get("/contacts")
        self.assertEqual(response.status_code, 200)

    def test_contacts_post_redirects_and_flashes(self):
        response = self.client.post(
            "/contacts",
            data={"name": "Іван", "email": "ivan@example.com", "message": "Привіт"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Дякуємо, Іван!".encode("utf-8"), response.data)

    def test_unknown_page_returns_404(self):
        response = self.client.get("/no-such-page")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
