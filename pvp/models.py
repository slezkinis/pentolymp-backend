from django.db import models
from django.contrib.auth import get_user_model
from tasks.models import Subject, Task


User = get_user_model()


class Queue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    
    class Meta:
        unique_together = ['user']
        verbose_name = "Очередь"
        verbose_name_plural = "Очереди"
    
    def __str__(self):
        return f"{self.user.username} - {self.subject.name}"


class MatchStatus(models.TextChoices):
    WAITING = "waiting", "Ожидание игрока"
    PLAYING = "playing", "Идет игра"
    FINISHED = "finished", "Завершен"
    CANCELLED = "cancelled", "Отменен"
    TECHNICAL_ERROR = "technical_error", "Техническая ошибка"


class MatchResult(models.TextChoices):
    PLAYER1_WIN = "player1_win", "Победа игрока 1"
    PLAYER2_WIN = "player2_win", "Победа игрока 2"
    DRAW = "draw", "Ничья"
    TECHNICAL = "technical", "Техническая ничья"


class Match(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    status = models.CharField("Статус", choices=MatchStatus.choices, default=MatchStatus.WAITING)
    result = models.CharField("Результат", choices=MatchResult.choices, blank=True, null=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Победитель")
    
    # Временные метки
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    started_at = models.DateTimeField("Начат", blank=True, null=True)
    finished_at = models.DateTimeField("Завершен", blank=True, null=True)
    
    # Настройки матча
    duration_minutes = models.IntegerField("Длительность (минуты)", default=15)
    max_tasks = models.IntegerField("Максимум задач", default=5)
    
    def __str__(self):
        return f"Матч #{self.id} - {self.subject.name} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = "PvP матч"
        verbose_name_plural = "PvP матчи"


class MatchParticipant(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Порядковый номер в матче (1 или 2)
    player_number = models.IntegerField("Номер игрока")
    
    # Статистика матча
    tasks_solved = models.IntegerField("Решено задач", default=0)
    time_taken = models.FloatField("Затрачено времени (секунды)", default=0)
    
    # Текущие задачи в матче
    current_task_index = models.IntegerField("Текущий индекс задачи", default=0)
    
    # Время подключения к матчу
    connected_at = models.DateTimeField("Подключен", auto_now_add=True)
    
    class Meta:
        unique_together = ['match', 'user']
        verbose_name = "Участник матча"
        verbose_name_plural = "Участники матча"
    
    def __str__(self):
        return f"{self.user.username} в матче #{self.match.id}"


class MatchTask(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="match_tasks")
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    order = models.IntegerField("Порядковый номер")
    
    class Meta:
        unique_together = ['match', 'order']
        verbose_name = "Задача матча"
        verbose_name_plural = "Задачи матча"
    
    def __str__(self):
        return f"Задача {self.order} для матча #{self.match.id}"


class PvpSettings(models.Model):
    name = models.CharField("Название настройки", max_length=50, unique=True)
    duration_minutes = models.IntegerField("Длительность (минуты)", default=15)
    max_tasks = models.IntegerField("Максимум задач", default=5)
    k_factor = models.IntegerField("K-фактор Elo", default=32)
    initial_rating = models.IntegerField("Начальный рейтинг", default=1000)
    
    is_active = models.BooleanField("Активна", default=True)
    
    class Meta:
        verbose_name = "Настройки PvP"
        verbose_name_plural = "Настройки PvP"
    
    def __str__(self):
        return f"{self.name} ({self.duration_minutes}мин, {self.max_tasks}задач)"