from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False)
    username = models.CharField(unique=True, blank=False, max_length=20)
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='user',
    )
    
    solved_tasks = models.ManyToManyField(
        'tasks.Task',
        verbose_name='Решённые задачи',
        blank=True
    )
    
    USERNAME_FIELD = 'username'
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Создаем рейтинг только для нового пользователя
        if is_new:
            Rating.objects.create(user=self)


class Rating(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rating')
    score = models.IntegerField('Рейтинг', default=1000)
    matches_played = models.IntegerField('Сыграно матчей', default=0)
    matches_won = models.IntegerField('Побед', default=0)
    matches_lost = models.IntegerField('Поражений', default=0)
    matches_drawn = models.IntegerField('Ничьи', default=0)
    
    def update_rating(self, opponent_rating, result, k_factor=32):
        """Обновление рейтинга по формуле Elo"""
        if result == 'technical':  # техническая ничья или отмена
            return
        
        expected_score = 1 / (1 + 10 ** ((opponent_rating - self.score) / 400))
        
        if result == 'win':
            actual_score = 1.0
        elif result == 'loss':
            actual_score = 0.0
        else:  # draw
            actual_score = 0.5
        
        self.score += round(k_factor * (actual_score - expected_score))
        self.matches_played += 1
        
        if result == 'win':
            self.matches_won += 1
        elif result == 'loss':
            self.matches_lost += 1
        else:
            self.matches_drawn += 1
        
        self.save()
    
    def __str__(self):
        return f"{self.user.username}: {self.score}"

    class Meta:
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'