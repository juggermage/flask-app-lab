import os
import tempfile
import unittest
import logging

from app import create_app


class MainViewsTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.tmp = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmp.name, "contact.log")
        self._saved = {k: self.app.config.get(k) for k in ("CONTACT_LOG_PATH", "WTF_CSRF_ENABLED")}
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, CONTACT_LOG_PATH=self.log_path)
        self.client = self.app.test_client()

    def tearDown(self):
        contact_logger = logging.getLogger("contact_form")
        for handler in list(contact_logger.handlers):
            contact_logger.removeHandler(handler)
            handler.close()
        self.app.config.update(self._saved)
        self.tmp.cleanup()

    @staticmethod
    def valid_data(**overrides):
        data = {
            "name": "Іван",
            "email": "ivan@example.com",
            "phone": "",
            "subject": "question",
            "message": "Привіт",
        }
        data.update(overrides)
        return data

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
        self.app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.get("/contacts")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="csrf_token"', response.data)

    def test_contacts_post_valid_redirects_flashes_and_logs(self):
        response = self.client.post("/contacts", data=self.valid_data())
        self.assertEqual(response.status_code, 302)  # Post/Redirect/Get
        self.assertTrue(response.headers["Location"].endswith("/contacts"))

        page = self.client.get("/contacts")
        self.assertIn("Дякуємо, Іван!".encode("utf-8"), page.data)
        self.assertIn(b"alert-success", page.data)

        with open(self.log_path, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("ivan@example.com", content)
        self.assertIn("Привіт", content)

    def test_contacts_name_length_validation(self):
        for bad in ("Ів", "Іванівський-Дуже"):
            with self.subTest(name=bad):
                response = self.client.post("/contacts", data=self.valid_data(name=bad))
                self.assertEqual(response.status_code, 200)
                self.assertIn("від 4 до 10 символів".encode("utf-8"), response.data)

    def test_contacts_invalid_email(self):
        response = self.client.post("/contacts", data=self.valid_data(email="not-an-email"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Невірний формат email".encode("utf-8"), response.data)
        self.assertIn(b"alert-danger", response.data)

    def test_contacts_phone_format(self):
        ok = self.client.post("/contacts", data=self.valid_data(phone="+380501234567"))
        self.assertEqual(ok.status_code, 302)
        for bad in ("0501234567", "+38050123456", "+3805012345678"):
            with self.subTest(phone=bad):
                response = self.client.post("/contacts", data=self.valid_data(phone=bad))
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"+380XXXXXXXXX", response.data)

    def test_contacts_message_too_long(self):
        response = self.client.post("/contacts", data=self.valid_data(message="a" * 501))
        self.assertEqual(response.status_code, 200)
        self.assertIn("500 символів".encode("utf-8"), response.data)

    def test_contacts_invalid_subject_rejected(self):
        response = self.client.post("/contacts", data=self.valid_data(subject="hack"))
        self.assertEqual(response.status_code, 200)

    def test_contacts_csrf_protection(self):
        self.app.config["WTF_CSRF_ENABLED"] = True
        response = self.client.post("/contacts", data=self.valid_data())
        self.assertEqual(response.status_code, 200)  # форма не пройшла валідацію
        self.assertFalse(os.path.exists(self.log_path))

    def test_contacts_log_failure_flashes_error(self):
        self.app.config["CONTACT_LOG_PATH"] = self.tmp.name  # це папка, а не файл -> OSError
        response = self.client.post("/contacts", data=self.valid_data(), follow_redirects=True)
        self.assertIn("Не вдалося записати".encode("utf-8"), response.data)
        self.assertIn(b"alert-danger", response.data)

    def test_unknown_page_returns_404(self):
        response = self.client.get("/no-such-page")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
