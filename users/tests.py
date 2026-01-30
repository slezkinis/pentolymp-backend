from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate
from users.models import Rating

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты для модели User"""

    def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_superuser)

    def test_create_user_without_username(self):
        """Тест создания пользователя без email"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='',
                email='test@example.com',
                password='testpass123'
            )


class RegistrationTest(TestCase):
    """Тесты для регистрации пользователя"""

    def test_register_user_success(self):
        """Тест успешной регистрации пользователя"""
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        self.assertTrue(User.objects.filter(email='new@example.com').exists())

    def test_register_user_email_exist(self):
        """Тест регистрации пользователя с существующим email"""
        User.objects.create_user(
            username='exisuser',
            email='exist@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='newuser',
                email='exist@example.com',
                password='testpass123'
            )

    def test_register_user_username_exist(self):
        """Тест регистрации пользователя с существующим username"""
        User.objects.create_user(
            username='existuser',
            email='exist@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username='existuser',
                email='new@example.com',
                password='testpass123'
            )


class LoginTest(TestCase):
    """Тесты для входа пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_user_success(self):
        """Тест успешного входа пользователя"""
        authenticated_user = authenticate(
            username=self.user.username,
            password='testpass123'
        )
        self.assertEqual(authenticated_user, self.user)

    def test_login_user_wrong_password(self):
        """Тест входа с неверным паролем"""
        authenticated_user = authenticate(
            username=self.user.email,
            password='wtestpass123'
        )
        self.assertIsNone(authenticated_user)

    def test_login_user_noexist(self):
        """Тест входа несуществующего пользователя"""
        authenticated_user = authenticate(
            username='noexistuser',
            password='testpass123'
        )
        self.assertIsNone(authenticated_user)


class UsernameChangeTest(TestCase):
    """Тесты для смены никнейма пользователя"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_change_username_success(self):
        """Тест успешной смены никнейма"""
        self.user.username = 'newusername'
        self.user.save()
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.username, 'newusername')

    def test_change_username_exist(self):
        """Тест смены никнейма на уже существующий"""
        User.objects.create_user(
            username='existuser',
            email='exist@example.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            self.user.username = 'existuser'
            self.user.save()

