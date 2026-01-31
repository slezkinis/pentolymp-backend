from django.apps import AppConfig
from django.db.utils import OperationalError

class PvpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pvp'
    verbose_name = 'PvP матчи'

    # TODO вынести в management комманду
    def ready(self):
        from .models import PvpSettings
        try:
            PvpSettings.objects.get(is_active=True)
        except PvpSettings.DoesNotExist:
            PvpSettings.objects.create(
                name='default',
                duration_minutes=15,
                max_tasks=5,
                k_factor=32,
                initial_rating=1000
            )
        except OperationalError:
            print("Database is not ready yet")
            pass
