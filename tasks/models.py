from django.db import models
from tinymce import models as tinymce_models


class Difficulty_Level(models.TextChoices):
    EASY = "Easy", "Легко"
    MEDIUM = "Medium", "Средне"
    HARD = "Hard", "Трудно"


class Task(models.Model):
    name = models.CharField("Название", max_length=30)
    description = tinymce_models.HTMLField("Условие задачи")
    answer = models.CharField("Правильный ответ")
    topic = models.ForeignKey("Topic", on_delete=models.CASCADE, verbose_name="Тема", related_name="tasks")
    difficulty_level = models.CharField("Уровень сложности", choices=Difficulty_Level.choices)
    tip = models.TextField("Подсказка", blank=True, null=True)

    def is_solved(self, user):
        return user.solved_tasks.filter(id=self.id).exists()
    
    def check_answer(self, answer):
        return self.answer == answer
    
    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"


class Subject(models.Model):
    name = models.CharField("Название", max_length=30)

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"


class Topic(models.Model):
    name = models.CharField("Название", max_length=30)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет", related_name="topics")

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"
