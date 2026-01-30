from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from .models import Task, Subject, Topic, Difficulty_Level
from .serializers import (
    TaskSerializer,
    CheckAnswerSerializer,
    SubjectSerializer,
    TopicSerializer,
    TipSerializer,
)

User = get_user_model()


# --- Модели ---


class SubjectModelTest(TestCase):
    """Тесты для модели Subject."""

    def test_create_subject(self):
        """Тест создания предмета."""
        subject = Subject.objects.create(name="Математика")
        self.assertEqual(subject.name, "Математика")
        self.assertIsNotNone(subject.id)

    def test_subject_str(self):
        """Тест строкового представления предмета."""
        subject = Subject.objects.create(name="Физика")
        self.assertEqual(str(subject), "Физика")


class TopicModelTest(TestCase):
    """Тесты для модели Topic."""

    def setUp(self):
        self.subject = Subject.objects.create(name="Математика")

    def test_create_topic(self):
        """Тест создания темы."""
        topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.assertEqual(topic.name, "Алгебра")
        self.assertEqual(topic.subject, self.subject)
        self.assertIsNotNone(topic.id)

    def test_topic_str(self):
        """Тест строкового представления темы."""
        topic = Topic.objects.create(name="Геометрия", subject=self.subject)
        self.assertEqual(str(topic), "Геометрия")

    def test_topic_related_tasks(self):
        """Тема связана с задачами через related_name tasks."""
        topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.assertEqual(topic.tasks.count(), 0)
        Task.objects.create(
            name="Задача 1",
            description="Условие",
            answer="42",
            topic=topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertEqual(topic.tasks.count(), 1)


class TaskModelTest(TestCase):
    """Тесты для модели Task."""

    def setUp(self):
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_create_task(self):
        """Тест создания задачи."""
        task = Task.objects.create(
            name="Найти корень",
            description="<p>Решите уравнение</p>",
            answer="5",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertEqual(task.name, "Найти корень")
        self.assertEqual(task.answer, "5")
        self.assertEqual(task.topic, self.topic)
        self.assertEqual(task.difficulty_level, Difficulty_Level.EASY)
        self.assertIsNotNone(task.id)

    def test_create_task_with_tip(self):
        """Тест создания задачи с подсказкой."""
        task = Task.objects.create(
            name="Задача с подсказкой",
            description="Условие",
            answer="10",
            topic=self.topic,
            difficulty_level=Difficulty_Level.MEDIUM,
            tip="Попробуйте подставить x=2",
        )
        self.assertEqual(task.tip, "Попробуйте подставить x=2")

    def test_create_task_tip_optional(self):
        """Подсказка может быть пустой."""
        task = Task.objects.create(
            name="Без подсказки",
            description="Условие",
            answer="1",
            topic=self.topic,
            difficulty_level=Difficulty_Level.HARD,
        )
        self.assertIsNone(task.tip)

    def test_task_str(self):
        """Тест строкового представления задачи."""
        task = Task.objects.create(
            name="Тестовая задача",
            description="Условие",
            answer="0",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertEqual(str(task), "Тестовая задача")

    def test_check_answer_correct(self):
        """Проверка ответа — верный ответ возвращает True."""
        task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertTrue(task.check_answer("42"))

    def test_check_answer_incorrect(self):
        """Проверка ответа — неверный ответ возвращает False."""
        task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertFalse(task.check_answer("43"))
        self.assertFalse(task.check_answer(""))

    def test_is_solved_false_when_not_solved(self):
        """is_solved возвращает False, если пользователь не решил задачу."""
        task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.assertFalse(task.is_solved(self.user))

    def test_is_solved_true_when_solved(self):
        """is_solved возвращает True, если пользователь решил задачу."""
        task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        self.user.solved_tasks.add(task)
        self.assertTrue(task.is_solved(self.user))

    def test_task_cascade_delete_with_topic(self):
        """При удалении темы удаляются связанные задачи."""
        task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="1",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        task_id = task.id
        self.topic.delete()
        self.assertFalse(Task.objects.filter(id=task_id).exists())


# --- Сериализаторы ---


class TaskSerializerTest(TestCase):
    """Тесты для TaskSerializer."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Тестовая задача",
            description="<p>Условие</p>",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )

    def test_serializer_fields(self):
        """Проверка полей в сериализованных данных."""
        request = type("Request", (), {"user": self.user})()
        serializer = TaskSerializer(
            self.task, context={"request": request}
        )
        data = serializer.data
        self.assertIn("id", data)
        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertIn("difficulty_level", data)
        self.assertIn("is_solved", data)
        self.assertIn("topic", data)
        self.assertIn("subject", data)
        self.assertEqual(data["name"], "Тестовая задача")
        self.assertEqual(data["topic"], "Алгебра")
        self.assertEqual(data["subject"], "Математика")
        self.assertEqual(data["difficulty_level"], Difficulty_Level.EASY)

    def test_is_solved_false_in_representation(self):
        """is_solved False для нерешённой задачи."""
        request = type("Request", (), {"user": self.user})()
        serializer = TaskSerializer(
            self.task, context={"request": request}
        )
        self.assertFalse(serializer.data["is_solved"])

    def test_is_solved_true_in_representation(self):
        """is_solved True для решённой задачи."""
        self.user.solved_tasks.add(self.task)
        request = type("Request", (), {"user": self.user})()
        serializer = TaskSerializer(
            self.task, context={"request": request}
        )
        self.assertTrue(serializer.data["is_solved"])


class CheckAnswerSerializerTest(TestCase):
    """Тесты для CheckAnswerSerializer."""

    def setUp(self):
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )

    def test_valid_data(self):
        """Валидные данные с полем answer."""
        serializer = CheckAnswerSerializer(data={"answer": "42"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["answer"], "42")

    def test_missing_answer_invalid(self):
        """Отсутствие answer делает данные невалидными."""
        serializer = CheckAnswerSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("answer", serializer.errors)

    def test_check_correct_answer(self):
        """Метод check возвращает True для верного ответа."""
        serializer = CheckAnswerSerializer(data={"answer": "42"})
        serializer.is_valid()
        self.assertTrue(serializer.check(self.task, "42"))

    def test_check_incorrect_answer(self):
        """Метод check возвращает False для неверного ответа."""
        serializer = CheckAnswerSerializer(data={"answer": "100"})
        serializer.is_valid()
        self.assertFalse(serializer.check(self.task, "100"))


class SubjectSerializerTest(TestCase):
    """Тесты для SubjectSerializer."""

    def test_serializer_fields(self):
        """Проверка полей сериализатора Subject."""
        subject = Subject.objects.create(name="Математика")
        serializer = SubjectSerializer(subject)
        self.assertEqual(serializer.data["id"], subject.id)
        self.assertEqual(serializer.data["name"], "Математика")


class TopicSerializerTest(TestCase):
    """Тесты для TopicSerializer."""

    def test_serializer_fields(self):
        """Проверка полей сериализатора Topic."""
        subject = Subject.objects.create(name="Математика")
        topic = Topic.objects.create(name="Алгебра", subject=subject)
        serializer = TopicSerializer(topic)
        self.assertEqual(serializer.data["id"], topic.id)
        self.assertEqual(serializer.data["name"], "Алгебра")


class TipSerializerTest(TestCase):
    """Тесты для TipSerializer."""

    def setUp(self):
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
            tip="Подсказка к задаче",
        )

    def test_serializer_fields(self):
        """TipSerializer возвращает id и tip."""
        serializer = TipSerializer(self.task)
        self.assertEqual(serializer.data["id"], self.task.id)
        self.assertEqual(serializer.data["tip"], "Подсказка к задаче")

    def test_tip_null_serializes(self):
        """Задача без подсказки — tip может быть null."""
        task_no_tip = Task.objects.create(
            name="Без подсказки",
            description="Условие",
            answer="1",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )
        serializer = TipSerializer(task_no_tip)
        self.assertIsNone(serializer.data["tip"])


# --- API Views ---


class TasksViewAPITest(TestCase):
    """Тесты для API списка задач (TasksView)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Тестовая задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )

    def test_list_requires_authentication(self):
        """Список задач доступен только авторизованным."""
        url = reverse("tasks")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_authenticated_returns_200(self):
        """Авторизованный пользователь получает список задач."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data.get("results"), list)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_list_filter_by_name(self):
        """Фильтрация задач по имени."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks") + "?name=Тестовая"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Тестовая задача")

    def test_list_filter_by_name_no_match(self):
        """Фильтр по имени без совпадений возвращает пустой список."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks") + "?name=НесуществующаяЗадача"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_list_filter_by_difficulty_level(self):
        """Фильтрация по уровню сложности."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks") + "?difficulty_level=Easy"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["difficulty_level"], "Easy")

    def test_list_filter_by_topic_id(self):
        """Фильтрация по topic_id."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks") + f"?topic_id={self.topic.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["topic"], "Алгебра")

    def test_list_filter_by_subject_id(self):
        """Фильтрация по subject_id."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tasks") + f"?subject_id={self.subject.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)


class TaskViewAPITest(TestCase):
    """Тесты для API одной задачи и проверки ответа (TaskView)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Тестовая задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
        )

    def test_get_task_requires_authentication(self):
        """Получение задачи требует авторизации."""
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_task_authenticated_returns_200(self):
        """Авторизованный пользователь получает задачу по id."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task.id)
        self.assertEqual(response.data["name"], "Тестовая задача")
        self.assertIn("is_solved", response.data)

    def test_get_task_shows_is_solved_after_correct_answer(self):
        """После верного ответа GET задачи возвращает is_solved: true."""
        self.client.force_authenticate(user=self.user)
        self.client.post(
            reverse("task", kwargs={"pk": self.task.id}),
            {"answer": "42"},
            format="json",
        )
        response = self.client.get(reverse("task", kwargs={"pk": self.task.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_solved"])

    def test_get_task_not_found(self):
        """Несуществующий id задачи возвращает 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_check_answer_correct(self):
        """Проверка верного ответа возвращает is_correct: true."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.post(url, {"answer": "42"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_correct"])

    def test_post_check_answer_correct_adds_to_solved(self):
        """При верном ответе задача добавляется в solved_tasks пользователя."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        self.client.post(url, {"answer": "42"}, format="json")
        self.user.refresh_from_db()
        self.assertTrue(self.user.solved_tasks.filter(id=self.task.id).exists())

    def test_post_check_answer_incorrect(self):
        """Проверка неверного ответа возвращает is_correct: false."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.post(url, {"answer": "100"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_correct"])

    def test_post_check_answer_incorrect_does_not_add_solved(self):
        """При неверном ответе задача не добавляется в solved_tasks."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        self.client.post(url, {"answer": "wrong"}, format="json")
        self.assertFalse(self.user.solved_tasks.filter(id=self.task.id).exists())

    def test_post_check_answer_missing_answer_400(self):
        """Отправка без answer возвращает 400."""
        self.client.force_authenticate(user=self.user)
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_check_answer_requires_authentication(self):
        """Проверка ответа требует авторизации."""
        url = reverse("task", kwargs={"pk": self.task.id})
        response = self.client.post(url, {"answer": "42"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TipViewAPITest(TestCase):
    """Тесты для API подсказки (TipView)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Математика")
        self.topic = Topic.objects.create(name="Алгебра", subject=self.subject)
        self.task = Task.objects.create(
            name="Задача",
            description="Условие",
            answer="42",
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY,
            tip="Подсказка к задаче",
        )

    def test_get_tip_requires_authentication(self):
        """Получение подсказки требует авторизации."""
        url = reverse("tip", kwargs={"pk": self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_tip_authenticated_returns_200(self):
        """Авторизованный пользователь получает подсказку."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tip", kwargs={"pk": self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.task.id)
        self.assertEqual(response.data["tip"], "Подсказка к задаче")

    def test_get_tip_not_found(self):
        """Несуществующий id задачи возвращает 404."""
        self.client.force_authenticate(user=self.user)
        url = reverse("tip", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class SubjectsViewAPITest(TestCase):
    """Тесты для API списка предметов (SubjectsView)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        Subject.objects.create(name="Математика")
        Subject.objects.create(name="Физика")

    def test_list_subjects_requires_authentication(self):
        """Список предметов доступен только авторизованным."""
        url = reverse("subjects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_subjects_authenticated_returns_200(self):
        """Авторизованный пользователь получает список предметов."""
        self.client.force_authenticate(user=self.user)
        url = reverse("subjects")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)


class TopicsViewAPITest(TestCase):
    """Тесты для API списка тем по предмету (TopicsView)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Математика")
        Topic.objects.create(name="Алгебра", subject=self.subject)
        Topic.objects.create(name="Геометрия", subject=self.subject)

    def test_list_topics_requires_authentication(self):
        """Список тем доступен только авторизованным."""
        url = reverse("topics", kwargs={"subject_id": self.subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_topics_authenticated_returns_200(self):
        """Авторизованный пользователь получает темы по subject_id."""
        self.client.force_authenticate(user=self.user)
        url = reverse("topics", kwargs={"subject_id": self.subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_list_topics_empty_for_other_subject(self):
        """Для другого предмета возвращаются только его темы."""
        other_subject = Subject.objects.create(name="Физика")
        Topic.objects.create(name="Механика", subject=other_subject)
        self.client.force_authenticate(user=self.user)
        url = reverse("topics", kwargs={"subject_id": other_subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Механика")
