from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from pvp.models import (
    Queue, Match, MatchParticipant, MatchTask, PvpSettings,
    MatchStatus, MatchResult
)
from pvp.rating_service import RatingService
from pvp.serializers import (
    MatchSerializer, MatchParticipantSerializer, MatchTaskSerializer,
    CreateMatchSerializer, PvpSettingsSerializer, RatingSerializer
)
from tasks.models import Subject, Topic, Task, Difficulty_Level
from users.models import Rating

User = get_user_model()


class QueueModelTest(TestCase):
    """Тесты для модели Queue"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(name='Математика')

    def test_create_queue_entry(self):
        """Тест создания записи в очереди"""
        queue = Queue.objects.create(user=self.user, subject=self.subject)
        self.assertEqual(queue.user, self.user)
        self.assertEqual(queue.subject, self.subject)
        self.assertIsNotNone(queue.created_at)

    def test_unique_user_constraint(self):
        """Тест уникальности пользователя в очереди"""
        Queue.objects.create(user=self.user, subject=self.subject)

        # Попытка создать вторую запись для того же пользователя должна вызвать ошибку
        with self.assertRaises(Exception):
            Queue.objects.create(user=self.user, subject=self.subject)

    def test_queue_str_representation(self):
        """Тест строкового представления очереди"""
        queue = Queue.objects.create(user=self.user, subject=self.subject)
        expected = f"{self.user.username} - {self.subject.name}"
        self.assertEqual(str(queue), expected)


class MatchModelTest(TestCase):
    """Тесты для модели Match"""

    def setUp(self):
        self.subject = Subject.objects.create(name='Математика')
        self.user1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='testpass123'
        )

    def test_create_match(self):
        """Тест создания матча"""
        match = Match.objects.create(
            subject=self.subject,
            duration_minutes=15,
            max_tasks=5
        )
        self.assertEqual(match.subject, self.subject)
        self.assertEqual(match.status, MatchStatus.WAITING)
        self.assertEqual(match.duration_minutes, 15)
        self.assertEqual(match.max_tasks, 5)
        self.assertIsNone(match.result)
        self.assertIsNone(match.winner)

    def test_match_status_choices(self):
        """Тест выбора статуса матча"""
        match = Match.objects.create(subject=self.subject)
        match.status = MatchStatus.PLAYING
        match.save()
        self.assertEqual(match.status, MatchStatus.PLAYING)

        match.status = MatchStatus.FINISHED
        match.save()
        self.assertEqual(match.status, MatchStatus.FINISHED)

    def test_match_result_choices(self):
        """Тест выбора результата матча"""
        match = Match.objects.create(subject=self.subject)
        match.result = MatchResult.PLAYER1_WIN
        match.winner = self.user1
        match.save()
        self.assertEqual(match.result, MatchResult.PLAYER1_WIN)
        self.assertEqual(match.winner, self.user1)

    def test_match_str_representation(self):
        """Тест строкового представления матча"""
        match = Match.objects.create(subject=self.subject)
        expected = f"Матч #{match.id} - {self.subject.name} ({match.get_status_display()})"
        self.assertEqual(str(match), expected)


class MatchParticipantModelTest(TestCase):
    """Тесты для модели MatchParticipant"""

    def setUp(self):
        self.subject = Subject.objects.create(name='Математика')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.match = Match.objects.create(subject=self.subject)

    def test_create_participant(self):
        """Тест создания участника матча"""
        participant = MatchParticipant.objects.create(
            match=self.match,
            user=self.user,
            player_number=1
        )
        self.assertEqual(participant.match, self.match)
        self.assertEqual(participant.user, self.user)
        self.assertEqual(participant.player_number, 1)
        self.assertEqual(participant.tasks_solved, 0)
        self.assertEqual(participant.time_taken, 0)
        self.assertEqual(participant.current_task_index, 0)

    def test_unique_participant_constraint(self):
        """Тест уникальности участника в матче"""
        MatchParticipant.objects.create(
            match=self.match,
            user=self.user,
            player_number=1
        )

        # Попытка создать второго участника с тем же пользователем должна вызвать ошибку
        with self.assertRaises(Exception):
            MatchParticipant.objects.create(
                match=self.match,
                user=self.user,
                player_number=2
            )

    def test_participant_str_representation(self):
        """Тест строкового представления участника"""
        participant = MatchParticipant.objects.create(
            match=self.match,
            user=self.user,
            player_number=1
        )
        expected = f"{self.user.username} в матче #{self.match.id}"
        self.assertEqual(str(participant), expected)


class MatchTaskModelTest(TestCase):
    """Тесты для модели MatchTask"""

    def setUp(self):
        self.subject = Subject.objects.create(name='Математика')
        self.topic = Topic.objects.create(name='Алгебра', subject=self.subject)
        self.task = Task.objects.create(
            name='Тестовая задача',
            description='Описание задачи',
            answer='42',
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY
        )
        self.match = Match.objects.create(subject=self.subject)

    def test_create_match_task(self):
        """Тест создания задачи матча"""
        match_task = MatchTask.objects.create(
            match=self.match,
            task=self.task,
            order=1
        )
        self.assertEqual(match_task.match, self.match)
        self.assertEqual(match_task.task, self.task)
        self.assertEqual(match_task.order, 1)

    def test_unique_order_constraint(self):
        """Тест уникальности порядка задачи в матче"""
        MatchTask.objects.create(match=self.match, task=self.task, order=1)

        # Попытка создать вторую задачу с тем же порядком должна вызвать ошибку
        task2 = Task.objects.create(
            name='Вторая задача',
            description='Описание',
            answer='43',
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY
        )
        with self.assertRaises(Exception):
            MatchTask.objects.create(match=self.match, task=task2, order=1)


class PvpSettingsModelTest(TestCase):
    """Тесты для модели PvpSettings"""

    def test_create_settings(self):
        """Тест создания настроек PvP"""
        settings = PvpSettings.objects.create(
            name='default',
            duration_minutes=15,
            max_tasks=5,
            k_factor=32,
            initial_rating=1000
        )
        self.assertEqual(settings.name, 'default')
        self.assertEqual(settings.duration_minutes, 15)
        self.assertEqual(settings.max_tasks, 5)
        self.assertEqual(settings.k_factor, 32)
        self.assertEqual(settings.initial_rating, 1000)
        self.assertTrue(settings.is_active)

    def test_settings_str_representation(self):
        """Тест строкового представления настроек"""
        settings = PvpSettings.objects.create(
            name='default',
            duration_minutes=15,
            max_tasks=5
        )
        expected = "default (15мин, 5задач)"
        self.assertEqual(str(settings), expected)


class RatingServiceTest(TestCase):
    """Тесты для RatingService"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(name='Математика')
        self.match = Match.objects.create(subject=self.subject)

        # Рейтинги создаются автоматически при создании пользователя
        # Обновляем их до нужных значений
        rating1, _ = Rating.objects.get_or_create(user=self.user1)
        rating1.score = 1000
        rating1.save()

        rating2, _ = Rating.objects.get_or_create(user=self.user2)
        rating2.score = 1000
        rating2.save()

    def test_calculate_elo_rating_player1_win(self):
        """Тест расчета рейтинга при победе первого игрока"""
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            1000, 1000, 'player1_win', k_factor=32
        )

        # При равных рейтингах ожидаемый результат 0.5 для каждого
        # Победитель получает +16, проигравший -16
        self.assertGreater(new_rating1, 1000)
        self.assertLess(new_rating2, 1000)
        self.assertEqual(new_rating1 + new_rating2, 2000)  # Сумма рейтингов сохраняется

    def test_calculate_elo_rating_player2_win(self):
        """Тест расчета рейтинга при победе второго игрока"""
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            1000, 1000, 'player2_win', k_factor=32
        )

        self.assertLess(new_rating1, 1000)
        self.assertGreater(new_rating2, 1000)
        self.assertEqual(new_rating1 + new_rating2, 2000)

    def test_calculate_elo_rating_draw(self):
        """Тест расчета рейтинга при ничьей"""
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            1000, 1000, 'draw', k_factor=32
        )

        # При ничьей рейтинги не должны измениться (ожидаемый результат = фактический)
        self.assertEqual(new_rating1, 1000)
        self.assertEqual(new_rating2, 1000)

    def test_calculate_elo_rating_technical(self):
        """Тест расчета рейтинга при технической ошибке"""
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            1000, 1000, 'technical', k_factor=32
        )

        # При технической ошибке рейтинги не меняются
        self.assertEqual(new_rating1, 1000)
        self.assertEqual(new_rating2, 1000)

    def test_calculate_elo_rating_stronger_player_wins(self):
        """Тест расчета рейтинга когда сильный игрок побеждает"""
        # Сильный игрок (1200) побеждает слабого (800)
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            1200, 800, 'player1_win', k_factor=32
        )

        # Сильный игрок получает меньше очков за победу над слабым
        self.assertGreater(new_rating1, 1200)
        self.assertLess(new_rating2, 800)
        # Но изменение меньше, чем при равных рейтингах
        rating_change = new_rating1 - 1200
        self.assertLess(rating_change, 16)

    def test_calculate_elo_rating_weaker_player_wins(self):
        """Тест расчета рейтинга когда слабый игрок побеждает"""
        # Слабый игрок (800) побеждает сильного (1200)
        new_rating1, new_rating2 = RatingService.calculate_elo_rating(
            800, 1200, 'player1_win', k_factor=32
        )

        # Слабый игрок получает больше очков за победу над сильным
        self.assertGreater(new_rating1, 800)
        self.assertLess(new_rating2, 1200)
        rating_change = new_rating1 - 800
        self.assertGreater(rating_change, 16)

    def test_update_match_ratings_player1_win(self):
        """Тест обновления рейтингов после завершения матча (победа игрока 1)"""
        # Создаем участников
        participant1 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user2,
            player_number=2
        )

        # Завершаем матч
        self.match.status = MatchStatus.FINISHED
        self.match.result = MatchResult.PLAYER1_WIN
        self.match.winner = self.user1
        self.match.finished_at = timezone.now()
        self.match.save()

        # Обновляем рейтинги
        result = RatingService.update_match_ratings(self.match.id)
        self.assertTrue(result)

        # Проверяем обновленные рейтинги
        rating1 = Rating.objects.get(user=self.user1)
        rating2 = Rating.objects.get(user=self.user2)

        self.assertGreater(rating1.score, 1000)
        self.assertLess(rating2.score, 1000)
        self.assertEqual(rating1.matches_played, 1)
        self.assertEqual(rating2.matches_played, 1)
        self.assertEqual(rating1.matches_won, 1)
        self.assertEqual(rating2.matches_lost, 1)

    def test_update_match_ratings_draw(self):
        """Тест обновления рейтингов при ничьей"""
        participant1 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user2,
            player_number=2
        )

        self.match.status = MatchStatus.FINISHED
        self.match.result = MatchResult.DRAW
        self.match.finished_at = timezone.now()
        self.match.save()

        RatingService.update_match_ratings(self.match.id)

        rating1 = Rating.objects.get(user=self.user1)
        rating2 = Rating.objects.get(user=self.user2)

        # При ничьей рейтинги не должны сильно измениться
        self.assertEqual(rating1.matches_played, 1)
        self.assertEqual(rating2.matches_played, 1)
        self.assertEqual(rating1.matches_drawn, 1)
        self.assertEqual(rating2.matches_drawn, 1)

    def test_update_match_ratings_technical(self):
        """Тест обновления рейтингов при технической ошибке"""
        participant1 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user2,
            player_number=2
        )

        self.match.status = MatchStatus.FINISHED
        self.match.result = MatchResult.TECHNICAL
        self.match.finished_at = timezone.now()
        self.match.save()

        RatingService.update_match_ratings(self.match.id)

        rating1 = Rating.objects.get(user=self.user1)
        rating2 = Rating.objects.get(user=self.user2)

        # При технической ошибке рейтинги не меняются
        self.assertEqual(rating1.score, 1000)
        self.assertEqual(rating2.score, 1000)
        # Но матчи все равно засчитываются
        self.assertEqual(rating1.matches_played, 1)
        self.assertEqual(rating2.matches_played, 1)

    def test_get_leaderboard(self):
        """Тест получения таблицы лидеров"""
        # Создаем еще несколько пользователей с разными рейтингами
        user3 = User.objects.create_user(
            username='player3',
            email='player3@example.com',
            password='testpass123'
        )
        user4 = User.objects.create_user(
            username='player4',
            email='player4@example.com',
            password='testpass123'
        )

        # Рейтинги создаются автоматически, обновляем их
        rating3, _ = Rating.objects.get_or_create(user=user3)
        rating3.score = 1200
        rating3.save()

        rating4, _ = Rating.objects.get_or_create(user=user4)
        rating4.score = 800
        rating4.save()

        leaderboard = RatingService.get_leaderboard(limit=10)

        self.assertEqual(len(leaderboard), 4)
        # Проверяем сортировку по убыванию рейтинга
        self.assertEqual(leaderboard[0]['rating'], 1200)
        self.assertEqual(leaderboard[1]['rating'], 1000)
        self.assertEqual(leaderboard[2]['rating'], 1000)
        self.assertEqual(leaderboard[3]['rating'], 800)

    def test_get_leaderboard_with_subject_filter(self):
        """Тест получения таблицы лидеров с фильтром по предмету"""
        # Создаем матч и участников
        participant1 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user2,
            player_number=2
        )

        leaderboard = RatingService.get_leaderboard(limit=10, subject_id=self.subject.id)

        # Должны быть только пользователи, участвовавшие в матчах по этому предмету
        self.assertGreaterEqual(len(leaderboard), 2)
        user_ids = [entry['user_id'] for entry in leaderboard]
        self.assertIn(self.user1.id, user_ids)
        self.assertIn(self.user2.id, user_ids)


class SerializerTest(TestCase):
    """Тесты для сериализаторов"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(name='Математика')
        self.topic = Topic.objects.create(name='Алгебра', subject=self.subject)
        self.task = Task.objects.create(
            name='Тестовая задача',
            description='Описание задачи',
            answer='42',
            topic=self.topic,
            difficulty_level=Difficulty_Level.EASY
        )
        self.match = Match.objects.create(subject=self.subject)
        self.participant1 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user1,
            player_number=1
        )
        self.participant2 = MatchParticipant.objects.create(
            match=self.match,
            user=self.user2,
            player_number=2
        )
        self.match_task = MatchTask.objects.create(
            match=self.match,
            task=self.task,
            order=1
        )

    def test_match_serializer(self):
        """Тест сериализатора Match"""
        serializer = MatchSerializer(self.match)
        data = serializer.data

        self.assertEqual(data['id'], self.match.id)
        self.assertEqual(data['subject']['name'], self.subject.name)
        self.assertEqual(data['status'], self.match.status)
        self.assertEqual(len(data['participants']), 2)
        self.assertEqual(len(data['match_tasks']), 1)

    def test_match_participant_serializer(self):
        """Тест сериализатора MatchParticipant"""
        serializer = MatchParticipantSerializer(self.participant1)
        data = serializer.data

        self.assertEqual(data['user']['username'], self.user1.username)
        self.assertEqual(data['player_number'], 1)
        self.assertEqual(data['tasks_solved'], 0)

    def test_match_task_serializer(self):
        """Тест сериализатора MatchTask"""
        serializer = MatchTaskSerializer(self.match_task)
        data = serializer.data

        self.assertEqual(data['task']['name'], self.task.name)
        self.assertEqual(data['order'], 1)

    def test_create_match_serializer_valid(self):
        """Тест валидного CreateMatchSerializer"""
        serializer = CreateMatchSerializer(data={
            'subject_id': self.subject.id,
            'duration_minutes': 20,
            'max_tasks': 10
        })
        self.assertTrue(serializer.is_valid())

    def test_create_match_serializer_invalid_duration(self):
        """Тест невалидного CreateMatchSerializer (неверная длительность)"""
        serializer = CreateMatchSerializer(data={
            'subject_id': self.subject.id,
            'duration_minutes': 100,  # Превышает максимум
            'max_tasks': 10
        })
        self.assertFalse(serializer.is_valid())

    def test_create_match_serializer_invalid_max_tasks(self):
        """Тест невалидного CreateMatchSerializer (неверное количество задач)"""
        serializer = CreateMatchSerializer(data={
            'subject_id': self.subject.id,
            'duration_minutes': 15,
            'max_tasks': 25  # Превышает максимум
        })
        self.assertFalse(serializer.is_valid())

    def test_pvp_settings_serializer(self):
        """Тест сериализатора PvpSettings"""
        settings = PvpSettings.objects.create(
            name='default',
            duration_minutes=15,
            max_tasks=5,
            k_factor=32,
            initial_rating=1000
        )
        serializer = PvpSettingsSerializer(settings)
        data = serializer.data

        self.assertEqual(data['name'], 'default')
        self.assertEqual(data['duration_minutes'], 15)
        self.assertEqual(data['max_tasks'], 5)
        self.assertEqual(data['k_factor'], 32)
        self.assertEqual(data['initial_rating'], 1000)
        self.assertTrue(data['is_active'])


class MatchFlowTest(TestCase):
    """Интеграционные тесты для полного цикла матча"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='player1',
            email='player1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='player2',
            email='player2@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(name='Математика')
        self.topic = Topic.objects.create(name='Алгебра', subject=self.subject)

        # Создаем задачи
        self.tasks = []
        for i in range(5):
            task = Task.objects.create(
                name=f'Задача {i + 1}',
                description=f'Описание задачи {i + 1}',
                answer=f'answer{i + 1}',
                topic=self.topic,
                difficulty_level=Difficulty_Level.EASY
            )
            self.tasks.append(task)

    def test_complete_match_flow(self):
        """Тест полного цикла матча от создания до завершения"""
        # Создаем матч
        match = Match.objects.create(
            subject=self.subject,
            duration_minutes=15,
            max_tasks=5
        )
        self.assertEqual(match.status, MatchStatus.WAITING)

        # Добавляем участников
        participant1 = MatchParticipant.objects.create(
            match=match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=match,
            user=self.user2,
            player_number=2
        )

        # Добавляем задачи
        for i, task in enumerate(self.tasks, 1):
            MatchTask.objects.create(match=match, task=task, order=i)

        # Начинаем матч
        match.status = MatchStatus.PLAYING
        match.started_at = timezone.now()
        match.save()

        # Игрок 1 решает 3 задачи
        participant1.tasks_solved = 3
        participant1.current_task_index = 3
        participant1.save()

        # Игрок 2 решает 2 задачи
        participant2.tasks_solved = 2
        participant2.current_task_index = 2
        participant2.save()

        # Завершаем матч
        match.status = MatchStatus.FINISHED
        match.result = MatchResult.PLAYER1_WIN
        match.winner = self.user1
        match.finished_at = timezone.now()
        match.save()

        # Проверяем результаты
        self.assertEqual(match.status, MatchStatus.FINISHED)
        self.assertEqual(match.result, MatchResult.PLAYER1_WIN)
        self.assertEqual(match.winner, self.user1)

        # Обновляем рейтинги
        RatingService.update_match_ratings(match.id)

        rating1 = Rating.objects.get(user=self.user1)
        rating2 = Rating.objects.get(user=self.user2)

        self.assertGreater(rating1.score, 1000)
        self.assertLess(rating2.score, 1000)
        self.assertEqual(rating1.matches_won, 1)
        self.assertEqual(rating2.matches_lost, 1)

    def test_match_draw_flow(self):
        """Тест цикла матча с ничьей"""
        match = Match.objects.create(subject=self.subject)

        participant1 = MatchParticipant.objects.create(
            match=match,
            user=self.user1,
            player_number=1
        )
        participant2 = MatchParticipant.objects.create(
            match=match,
            user=self.user2,
            player_number=2
        )

        # Оба решают одинаковое количество задач
        participant1.tasks_solved = 3
        participant2.tasks_solved = 3
        participant1.save()
        participant2.save()

        match.status = MatchStatus.FINISHED
        match.result = MatchResult.DRAW
        match.finished_at = timezone.now()
        match.save()

        RatingService.update_match_ratings(match.id)

        rating1 = Rating.objects.get(user=self.user1)
        rating2 = Rating.objects.get(user=self.user2)

        self.assertEqual(rating1.matches_drawn, 1)
        self.assertEqual(rating2.matches_drawn, 1)
