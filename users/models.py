# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

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