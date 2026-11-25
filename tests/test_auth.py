import unittest

from app import create_app, db
from app.users.models import User


class AuthTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            user = User(username="user1", email="user1@example.com")
            user.set_password("12345")
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login(self, username="user1", password="12345"):
        return self.client.post(
            "/users/login",
            data={"username": username, "password": password},
            follow_redirects=True,
        )

    def test_login_page(self):
        self.assertEqual(self.client.get("/users/login").status_code, 200)

    def test_profile_requires_login(self):
        r = self.client.get("/users/profile")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/users/login", r.headers["Location"])
        r = self.client.get("/users/profile", follow_redirects=True)
        self.assertIn(b"alert-warning", r.data)

    def test_wrong_login(self):
        r = self.login(password="bad")
        self.assertIn(b"Wrong data!", r.data)
        self.assertIn(b"alert-danger", r.data)

    def test_successful_login_and_profile(self):
        r = self.login()
        self.assertIn(b"alert-success", r.data)
        self.assertIn("Ласкаво просимо".encode(), r.data)
        self.assertIn(b"user1", r.data)

    def test_logout(self):
        self.login()
        r = self.client.post("/users/logout", follow_redirects=True)
        self.assertIn("Ви вийшли".encode(), r.data)
        self.assertEqual(self.client.get("/users/profile").status_code, 302)

    def test_add_and_delete_cookie(self):
        self.login()
        r = self.client.post("/users/cookies/add",
                             data={"key": "foo", "value": "bar", "max_age": "60"},
                             follow_redirects=True)
        self.assertIn("Кукі &#39;foo&#39; додано".encode(), r.data)
        self.assertIn(b"foo", r.data)
        r = self.client.post("/users/cookies/delete", data={"key": "foo"}, follow_redirects=True)
        self.assertIn("видалено".encode(), r.data)
        r = self.client.post("/users/cookies/delete", data={"key": "foo"}, follow_redirects=True)
        self.assertIn("не знайдено".encode(), r.data)

    def test_delete_all_keeps_session(self):
        self.login()
        self.client.post("/users/cookies/add", data={"key": "a", "value": "1"})
        r = self.client.post("/users/cookies/delete-all", follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Ласкаво просимо".encode(), r.data)  # досі авторизований

    def test_theme_persists(self):
        self.login()
        r = self.client.get("/users/theme/dark", follow_redirects=True)
        self.assertIn(b'data-bs-theme="dark"', r.data)
        r = self.client.get("/users/profile")  # наступний візит
        self.assertIn(b'data-bs-theme="dark"', r.data)
        self.client.get("/users/theme/light")
        r = self.client.get("/users/profile")
        self.assertIn(b'data-bs-theme="light"', r.data)

    def test_invalid_theme(self):
        self.login()
        r = self.client.get("/users/theme/pink", follow_redirects=True)
        self.assertIn("Невідома".encode(), r.data)


if __name__ == "__main__":
    unittest.main()
