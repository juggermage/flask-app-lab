import unittest
from app import create_app, db, bcrypt
from app.users.models import User


class Lab9Tests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
        self.data = dict(username='student9', email='student9@example.com',
                         password='Secret123', confirm_password='Secret123')

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def register(self, **changes):
        return self.client.post('/users/register', data={**self.data, **changes})

    def login(self, password='Secret123', **extra):
        return self.client.post('/users/login', data=dict(username='student9', password=password, **extra))

    def test_views(self):
        for path in ('/users/register', '/users/login'):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_registration_and_hash(self):
        self.assertEqual(self.register().status_code, 302)
        with self.app.app_context():
            user = db.session.scalar(db.select(User))
            self.assertEqual(user.email, self.data['email'])
            self.assertTrue(user.password.startswith('$2b$'))
            self.assertTrue(bcrypt.check_password_hash(user.password, 'Secret123'))
            self.assertFalse(user.check_password('wrong'))

    def test_duplicate_username_and_email(self):
        self.register()
        self.assertEqual(self.register(email='other@example.com').status_code, 200)
        self.assertEqual(self.register(username='other9').status_code, 200)
        with self.app.app_context():
            self.assertEqual(len(db.session.scalars(db.select(User)).all()), 1)

    def test_invalid_registration(self):
        for changes in (dict(username='1bad'), dict(email='bad'), dict(confirm_password='wrong'), dict(password='short', confirm_password='short')):
            self.assertEqual(self.register(**changes).status_code, 200)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(db.select(User)))

    def test_login_logout_and_protection(self):
        self.register()
        for path in ('/users/account', '/users/list'):
            self.assertIn('/users/login', self.client.get(path).location)
        self.assertEqual(self.login('wrong').status_code, 200)
        self.assertIn('/users/account', self.login().location)
        self.assertIn(b'student9@example.com', self.client.get('/users/account').data)
        self.assertIn(b'student9', self.client.get('/users/list').data)
        self.assertIn('/users/account', self.client.get('/users/register').location)
        self.assertIn('/users/account', self.client.get('/users/login').location)
        self.assertEqual(self.client.post('/users/logout').status_code, 302)
        self.assertEqual(self.client.get('/users/account').status_code, 302)
        self.assertEqual(self.client.get('/users/list').status_code, 302)

    def test_remember_cookie(self):
        self.register()
        response = self.login(remember='y')
        self.assertTrue(any('remember_token=' in value for value in response.headers.getlist('Set-Cookie')))
        response = self.client.post('/users/logout')
        self.assertTrue(any('remember_token=;' in value for value in response.headers.getlist('Set-Cookie')))
