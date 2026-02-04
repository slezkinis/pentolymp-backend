from django.utils import timezone
from django.db import transaction
from django.db import OperationalError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from ..models import Queue, Match, MatchParticipant, MatchTask, PvpSettings
from tasks.models import Task

logger = logging.getLogger(__name__)


def process_waiting_players():
    """Периодическая проверка очереди и создание матчей"""
    try:
        channel_layer = get_channel_layer()
        queues_by_subject = Queue.objects.all().select_related('user__rating', 'subject').order_by('created_at')
        subject_groups = {}
        for queue in queues_by_subject:
            if queue.subject_id not in subject_groups:
                subject_groups[queue.subject_id] = []
            subject_groups[queue.subject_id].append(queue)
        
        for subject_id, players in subject_groups.items():
            if len(players) < 2:
                continue
            
            matched_players = set()
            current_time = timezone.now()
            
            for i, player1 in enumerate(players):
                if player1.user_id in matched_players:
                    continue
                    
                for player2 in players[i+1:]:
                    if player2.user_id in matched_players:
                        continue
                    
                    if should_create_match(player1, player2, current_time):
                        match_id = create_match_for_players(player1, player2)
                        if match_id:
                            matched_players.add(player1.user_id)
                            matched_players.add(player2.user_id)
                            notify_players(channel_layer, [player1.user_id, player2.user_id], match_id, player1.subject)
                            Queue.objects.filter(user_id__in=[player1.user_id, player2.user_id]).delete()
                            logger.info(f"Created match {match_id} between {player1.user.username} and {player2.user.username}")
                            break
    except OperationalError:
        pass
    except Exception as e:
        logger.error(f"Error in process_waiting_players: {e}")


def should_create_match(player1, player2, current_time):
    """Проверяет, стоит ли создавать матч между двумя игроками"""
    try:
        settings = PvpSettings.objects.filter(is_active=True).first()
        rating_diff = abs(player1.user.rating.score - player2.user.rating.score)
        
        if rating_diff <= settings.max_rating_diff_for_nodelay:
            return True
        
        wait_time_1 = (current_time - player1.created_at).total_seconds()
        wait_time_2 = (current_time - player2.created_at).total_seconds()
        return wait_time_1 >= settings.min_wait_time and wait_time_2 >= settings.min_wait_time
        
    except Exception as e:
        logger.error(f"Error checking match conditions: {e}")
        return False


def create_match_for_players(player1, player2):
    """Создает матч для двух игроков"""
    try:
        with transaction.atomic():
            settings = PvpSettings.objects.filter(is_active=True).first()
            match = Match.objects.create(
                subject=player1.subject,
                duration_minutes=settings.duration_minutes if settings else 15,
                max_tasks=settings.max_tasks if settings else 5
            )
            
            MatchParticipant.objects.create(match=match, user=player1.user, player_number=1)
            MatchParticipant.objects.create(match=match, user=player2.user, player_number=2)
            
            tasks = Task.objects.filter(topic__subject=match.subject).order_by('?')[:match.max_tasks]
            for i, task in enumerate(tasks, 1):
                MatchTask.objects.create(match=match, task=task, order=i)
            
            return match.id
            
    except Exception as e:
        logger.error(f"Error creating match: {e}")
        return None


def notify_players(channel_layer, user_ids, match_id, subject):
    """Отправляет уведомления игрокам о найденном матче"""
    try:
        for user_id in user_ids:
            async_to_sync(channel_layer.group_send)(
                "pvp_queue",
                {
                    'type': 'opponent_match_found',
                    'opponent_id': user_id,
                    'match_id': match_id,
                    'subject': subject.name
                }
            )
    except Exception as e:
        logger.error(f"Error notifying players: {e}")