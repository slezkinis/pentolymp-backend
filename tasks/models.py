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
    difficulty_level = models.CharField("Уровень сложности", choices=Difficulty_Level.choices)

    def is_solved(self, user):
        return user.solved_tasks.filter(id=self.id).exists()
    
    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
    
