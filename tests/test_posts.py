import unittest
from datetime import datetime, timedelta

from app import create_app, db
from app.posts.models import Post, Tag
from app.users.models import User


class BaseCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
        self.user_id = self.make_user("user1")
        self.user2_id = self.make_user("user2")

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # ---------- допоміжні методи ----------

    def make_user(self, username):
        with self.app.app_context():
            user = User(username=username, email=f"{username}@ex.com")
            user.set_password("12345")
            db.session.add(user)
            db.session.commit()
            return user.id

    def make_tag(self, name):
        with self.app.app_context():
            tag = Tag(name=name)
            db.session.add(tag)
            db.session.commit()
            return tag.id

    def form_data(self, **overrides):
        data = {
            "title": "My first post",
            "content": "This is TDD!",
            "is_active": "y",
            "publish_date": "2024-11-21T20:45",
            "category": "tech",
            "author_id": str(self.user_id),
        }
        data.update(overrides)
        return data

    def make_post(self, **kwargs):
        values = {
            "title": "Test",
            "content": "Example post",
            "posted": datetime(2024, 11, 21, 12, 0),
            "category": "news",
        }
        values.update(kwargs)
        with self.app.app_context():
            post = Post(**values)
            db.session.add(post)
            db.session.commit()
            return post.id

    def get_post(self, post_id):
        with self.app.app_context():
            return db.session.get(Post, post_id)


class PostTestCase(BaseCase):

    # ---------- модель ----------

    def test_model_defaults_and_repr(self):
        with self.app.app_context():
            post = Post(title="Test", content="Example post")
            db.session.add(post)
            db.session.commit()
            self.assertTrue(post.is_active)
            self.assertIsNone(post.user)
            self.assertEqual(post.tags, [])
            self.assertEqual(post.category, "other")
            self.assertIsNotNone(post.posted)
            self.assertIn("Test", repr(post))

    # ---------- US01: створення ----------

    def test_create_post(self):
        response = self.client.post("/post/create", data=self.form_data(), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("успішно додано".encode(), response.data)  # flash-повідомлення

        with self.app.app_context():
            post = db.session.scalar(db.select(Post).where(Post.title == "My first post"))
            self.assertIsNotNone(post)
            self.assertEqual(post.content, "This is TDD!")
            self.assertEqual(post.category, "tech")
            self.assertEqual(post.posted, datetime(2024, 11, 21, 20, 45))
            self.assertEqual(post.user_id, self.user_id)
            self.assertEqual(post.user.username, "user1")

    def test_create_form_page(self):
        response = self.client.get("/post/create")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="title"', response.data)
        self.assertIn(b'name="author_id"', response.data)
        self.assertIn(b"user2", response.data)  # список авторів береться з БД
        self.assertIn(b'name="tags"', response.data)

    def test_create_post_redirects_to_list(self):
        response = self.client.post("/post/create", data=self.form_data())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/post"))

    def test_create_post_invalid_data(self):
        response = self.client.post("/post/create", data=self.form_data(title="", content=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("перевірте виділені поля".encode(), response.data)
        with self.app.app_context():
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_create_post_short_title(self):
        response = self.client.post("/post/create", data=self.form_data(title="a"))
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_create_post_invalid_category(self):
        response = self.client.post("/post/create", data=self.form_data(category="science"))
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_create_post_invalid_author(self):
        response = self.client.post("/post/create", data=self.form_data(author_id="999"))
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_create_post_with_tags(self):
        t1, t2 = self.make_tag("Tech"), self.make_tag("Art")
        self.client.post("/post/create", data=self.form_data(tags=[str(t1), str(t2)]))
        with self.app.app_context():
            post = db.session.scalar(db.select(Post))
            self.assertEqual(sorted(t.name for t in post.tags), ["Art", "Tech"])

    def test_create_post_invalid_tag(self):
        response = self.client.post("/post/create", data=self.form_data(tags=["999"]))
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_session_user_preselected_as_author(self):
        with self.client.session_transaction() as sess:
            sess["user"] = "user2"
        body = self.client.get("/post/create").data.decode()
        self.assertRegex(body, rf'<option selected value="{self.user2_id}">user2</option>')

    # ---------- US02: список ----------

    def test_list_posts(self):
        self.make_post(title="Old post", posted=datetime(2024, 1, 1))
        self.make_post(title="New post", posted=datetime(2024, 6, 1))
        response = self.client.get("/post")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode()
        self.assertIn("Old post", body)
        self.assertLess(body.index("New post"), body.index("Old post"))  # спадання за датою

    def test_list_hides_inactive_posts(self):
        self.make_post(title="Visible one")
        self.make_post(title="Hidden one", is_active=False)
        body = self.client.get("/post").data.decode()
        self.assertIn("Visible one", body)
        self.assertNotIn("Hidden one", body)

    def test_list_empty(self):
        response = self.client.get("/post")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Постів поки немає".encode(), response.data)

    def test_list_truncates_content(self):
        self.make_post(content="x" * 300)
        body = self.client.get("/post").data.decode()
        self.assertIn("x" * 100, body)
        self.assertNotIn("x" * 101, body)

    # ---------- US03: деталі ----------

    def test_view_post_detail(self):
        post_id = self.make_post(title="Detail title", content="Full content", user_id=self.user_id)
        response = self.client.get(f"/post/{post_id}")
        self.assertEqual(response.status_code, 200)
        for text in ("Detail title", "Full content", "user1"):
            self.assertIn(text.encode(), response.data)
        self.assertIn(f"/post/{post_id}/update".encode(), response.data)
        self.assertIn(f"/post/{post_id}/delete".encode(), response.data)

    def test_detail_shows_tags(self):
        post_id = self.make_post(title="Tagged")
        tag_id = self.make_tag("Science")
        with self.app.app_context():
            post = db.session.get(Post, post_id)
            post.tags.append(db.session.get(Tag, tag_id))
            db.session.commit()
        response = self.client.get(f"/post/{post_id}")
        self.assertIn(b'class="post-tag">Science</span>', response.data)

    # ---------- US04: редагування ----------

    def test_update_form_is_prefilled(self):
        post_id = self.make_post(title="Prefilled", posted=datetime(2024, 11, 21, 20, 45))
        response = self.client.get(f"/post/{post_id}/update")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Prefilled", response.data)
        self.assertIn(b"2024-11-21T20:45", response.data)

    def test_update_post(self):
        post_id = self.make_post(title="Before", user_id=self.user_id)
        tag_id = self.make_tag("Art")
        response = self.client.post(
            f"/post/{post_id}/update",
            data=self.form_data(title="After", content="Changed", category="publication",
                                publish_date="2025-02-03T04:05",
                                author_id=str(self.user2_id), tags=[str(tag_id)]),
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("оновлено".encode(), response.data)

        post = self.get_post(post_id)
        self.assertEqual(post.title, "After")
        self.assertEqual(post.content, "Changed")
        self.assertEqual(post.category, "publication")
        self.assertEqual(post.posted, datetime(2025, 2, 3, 4, 5))  # дату змінено, а не перезаписано
        self.assertEqual(post.user_id, self.user2_id)  # автора можна змінити
        with self.app.app_context():
            self.assertEqual([t.name for t in db.session.get(Post, post_id).tags], ["Art"])

    def test_update_form_preselects_author_and_tags(self):
        tag_id = self.make_tag("Art")
        post_id = self.make_post(user_id=self.user2_id)
        with self.app.app_context():
            post = db.session.get(Post, post_id)
            post.tags.append(db.session.get(Tag, tag_id))
            db.session.commit()
        body = self.client.get(f"/post/{post_id}/update").data.decode()
        self.assertIn(f'<option selected value="{self.user2_id}">user2</option>', body)
        self.assertIn(f'<option selected value="{tag_id}">Art</option>', body)

    def test_update_can_deactivate_post(self):
        post_id = self.make_post()
        data = self.form_data()
        del data["is_active"]  # непозначений чекбокс не надсилається
        self.client.post(f"/post/{post_id}/update", data=data)
        self.assertFalse(self.get_post(post_id).is_active)

    def test_update_post_invalid_data(self):
        post_id = self.make_post(title="Keep me")
        response = self.client.post(f"/post/{post_id}/update", data=self.form_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get_post(post_id).title, "Keep me")

    # ---------- US05: видалення ----------

    def test_delete_confirm_page(self):
        post_id = self.make_post(title="To delete")
        response = self.client.get(f"/post/{post_id}/delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Підтвердження видалення".encode(), response.data)
        self.assertIn(b"To delete", response.data)
        self.assertIsNotNone(self.get_post(post_id))  # GET нічого не видаляє

    def test_delete_post(self):
        post_id = self.make_post(title="To delete")
        response = self.client.post(f"/post/{post_id}/delete", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("успішно видалено".encode(), response.data)
        self.assertIsNone(self.get_post(post_id))

    def test_delete_requires_csrf_token(self):
        self.app.config["WTF_CSRF_ENABLED"] = True
        post_id = self.make_post()
        self.client.post(f"/post/{post_id}/delete")
        self.assertIsNotNone(self.get_post(post_id))

    # ---------- US06: 404 ----------

    def test_404_not_found(self):
        response = self.client.get("/post/999")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404", response.data)

    def test_404_unknown_page(self):
        self.assertEqual(self.client.get("/no/such/page").status_code, 404)

    def test_404_for_update_and_delete(self):
        self.assertEqual(self.client.get("/post/999/update").status_code, 404)
        self.assertEqual(self.client.post("/post/999/update", data=self.form_data()).status_code, 404)
        self.assertEqual(self.client.get("/post/999/delete").status_code, 404)
        self.assertEqual(self.client.post("/post/999/delete").status_code, 404)


class RelationshipsTestCase(BaseCase):
    """Лаб. 8: зв'язки User—Post (1:N) та Post—Tag (M:N)."""

    def test_user_posts_back_populates(self):
        self.make_post(title="A", user_id=self.user_id)
        self.make_post(title="B", user_id=self.user_id)
        self.make_post(title="C", user_id=self.user2_id)
        with self.app.app_context():
            u1 = db.session.get(User, self.user_id)
            self.assertEqual(sorted(p.title for p in u1.posts), ["A", "B"])
            self.assertEqual(u1.posts[0].user, u1)

    def test_deleting_user_deletes_posts(self):
        self.make_post(title="A", user_id=self.user_id)
        with self.app.app_context():
            db.session.delete(db.session.get(User, self.user_id))
            db.session.commit()
            self.assertEqual(db.session.scalars(db.select(Post)).all(), [])

    def test_many_to_many_both_directions(self):
        p1, p2 = self.make_post(title="P1"), self.make_post(title="P2")
        t_id = self.make_tag("Tech")
        with self.app.app_context():
            tag = db.session.get(Tag, t_id)
            tag.posts.append(db.session.get(Post, p1))
            tag.posts.append(db.session.get(Post, p2))
            db.session.commit()
            self.assertEqual([t.name for t in db.session.get(Post, p1).tags], ["Tech"])
            self.assertEqual(sorted(p.title for p in tag.posts), ["P1", "P2"])

    def test_password_is_hashed(self):
        with self.app.app_context():
            user = db.session.get(User, self.user_id)
            self.assertNotEqual(user.password, "12345")
            self.assertTrue(user.check_password("12345"))
            self.assertFalse(user.check_password("wrong"))
            self.assertEqual(repr(user), "User('user1@ex.com')")


class ConfigTestCase(unittest.TestCase):

    def test_testing_config_uses_memory_db(self):
        app = create_app("testing")
        self.assertTrue(app.config["TESTING"])
        self.assertEqual(app.config["SQLALCHEMY_DATABASE_URI"], "sqlite:///:memory:")

    def test_development_config(self):
        self.assertTrue(create_app("development").config["DEBUG"])

    def test_production_requires_secret_key(self):
        import os
        saved = os.environ.pop("SECRET_KEY", None)
        try:
            from app.config import ProductionConfig
            ProductionConfig.SECRET_KEY = None
            with self.assertRaises(RuntimeError):
                create_app("production")
            ProductionConfig.SECRET_KEY = "secret"
            app = create_app("production")
            self.assertFalse(app.config["DEBUG"])
            self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
        finally:
            if saved is not None:
                os.environ["SECRET_KEY"] = saved
            ProductionConfig.SECRET_KEY = saved


if __name__ == "__main__":
    unittest.main()
