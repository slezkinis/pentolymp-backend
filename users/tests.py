from django.test import TestCase
from django.contrib.auth import get_user_model, authenticate

from users.serializers import (
    UserSerializer, RegisterSerializer,
    LoginSerializer
)

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
        """Тест создания пользователя без username"""
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
        User.objects.create_user(
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


class UserSerializerTest(TestCase):
    """Тесты для UserSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser_rating',
            email='test2@example.com',
            password='testpass123'
        )
    
    def test_user_serializer(self):
        """Тест UserSerializer"""

        serializer = UserSerializer(instance=self.user)
        self.assertEqual(serializer.data['username'], self.user.username)
        self.assertEqual(serializer.data['email'], self.user.email)
        self.assertEqual(serializer.data['rating']["score"], 1000)

    def test_user_rating_serializer(self):
        """Тест рейтинга пользователя"""

        serializer = UserSerializer(instance=self.user)
        self.assertEqual(serializer.data['rating']["score"], 1000)
        self.assertEqual(serializer.data['rating']["matches_played"], 0)
        self.assertEqual(serializer.data['rating']["matches_won"], 0)
        self.assertEqual(serializer.data['rating']["matches_lost"], 0)
        self.assertEqual(serializer.data['rating']["matches_drawn"], 0)


class RegisterSerializerTest(TestCase):
    """Тесты для RegisterSerializer"""

    def test_register_serializer(self):
        """Тест RegisterSerializer"""

        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertTrue(serializer.is_valid(raise_exception=True))
        user = serializer.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
    
    def test_register_serializer_invalid(self):
        """Тест RegisterSerializer с несовпадающими паролями"""

        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass1234'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_email_exist(self):
        """Тест RegisterSerializer с существующим email"""

        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser2',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_username_exist(self):
        """Тест RegisterSerializer с существующим username"""

        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_without_username(self):
        """Тест RegisterSerializer без username"""

        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_without_email(self):
        """Тест RegisterSerializer без email"""

        serializer = RegisterSerializer(data={
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_without_password(self):
        """Тест RegisterSerializer без password"""

        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password2': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_register_serializer_without_password2(self):
        """Тест RegisterSerializer без password2"""

        serializer = RegisterSerializer(data={
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertFalse(serializer.is_valid())


class LoginSerializerTest(TestCase):
    """Тесты для LoginSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser3',
            email='test3@example.com',
            password='very_very_difficult_password'
        )

    def test_login_serializer(self):
        """Тест LoginSerializer"""

        serializer = LoginSerializer(data={
            'email': 'test3@example.com',
            'password': 'very_very_difficult_password'
        })
        self.assertTrue(serializer.is_valid(raise_exception=True))
    
    def test_login_serializer_invalid(self):
        """Тест LoginSerializer с неверным паролем"""

        serializer = LoginSerializer(data={
            'email': 'test3@example.com',
            'password': 'testpass1234'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_login_serializer_user_not_exist(self):
        """Тест LoginSerializer с несуществующим email"""

        serializer = LoginSerializer(data={
            'email': 'not_exist@example.com',
            'password': 'very_very_difficult_password'
        })
        self.assertFalse(serializer.is_valid())

    def test_login_serializer_without_username(self):
        """Тест LoginSerializer без email"""

        serializer = LoginSerializer(data={
            'password': 'very_very_difficult_password'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_login_serializer_without_password(self):
        """Тест LoginSerializer без password"""

        serializer = LoginSerializer(data={
            'email': 'test3@example.com'
        })
        self.assertFalse(serializer.is_valid())
