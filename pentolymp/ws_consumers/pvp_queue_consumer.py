import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.functions import Abs

from pvp.models import Match, MatchParticipant, MatchTask, PvpSettings, Queue
from tasks.models import Task, Subject
from users.models import Rating


User = get_user_model()


class PvpQueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.queue_group = "pvp_queue"
        await self.channel_layer.group_add(
            self.queue_group,
            self.channel_name
        )
        await self.set_up_rating()
        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.remove_from_queue()
            await self.channel_layer.group_discard(
                self.queue_group,
                self.channel_name
            )
        except Exception as e:
            pass
        
        

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        try:
            if message_type == 'find_match':
                subject_id = data.get('subject_id')
                await self.find_match(subject_id)
            elif message_type == 'cancel_search':
                await self.remove_from_queue()
                await self.send(text_data=json.dumps({
                    'type': 'queue_removed'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def remove_from_queue(self):
        try:
            Queue.objects.filter(user=self.user).delete()
            return True
        except Exception:
            print("Failed to remove from queue")
            return False

    @database_sync_to_async
    def create_queue_entry(self, subject):
        if Queue.objects.filter(user=self.user).exists():
            raise Exception("User already in queue")
        try:
            queue = Queue.objects.create(
                user=self.user,
                subject=subject
            )
            return queue
        except Exception:
            return None

    @database_sync_to_async
    def find_opponent_in_queue(self, subject_id):
        try:
            opponent = Queue.objects.filter(
                subject_id=subject_id
            ).exclude(user=self.user).annotate(diff=Abs(F('user__rating__score') - self.user.rating.score)).order_by('diff').first()
            
            if opponent:
                return opponent.user_id
            return None
        except Exception as e:
            print(e)
            return None

    @database_sync_to_async
    def delete_queue_entries(self, user_ids):
        try:
            Queue.objects.filter(user_id__in=user_ids).delete()
            return True
        except Exception:
            return False

    @database_sync_to_async
    def set_up_rating(self):
        Rating.objects.get_or_create(user=self.user)[0]

    async def find_match(self, subject_id):
        subject = await self.get_subject(subject_id)
        if not subject:
            raise Exception("Subject not found")
        
        queue_entry = await self.create_queue_entry(subject)
        if not queue_entry:
            raise Exception("Failed to create queue entry")
        
        opponent_user_id = await self.find_opponent_in_queue(subject_id)
        if opponent_user_id:
            match = await self.create_match(subject)
            if match:
                await self.add_participant(match, self.user)
                opponent_user = await self.get_user(opponent_user_id)
                if opponent_user:
                    await self.add_participant(match, opponent_user)
                    await self.generate_match_tasks(match)
                    await self.delete_queue_entries([self.user.id, opponent_user_id])
                    await self.send(text_data=json.dumps({
                        'type': 'match_found',
                        'match_id': match.id,
                        'subject': subject.name
                    }))
                    
                    await self.channel_layer.group_send(
                        "pvp_queue",
                        {
                            'type': 'opponent_match_found',
                            'opponent_id': opponent_user_id,
                            'match_id': match.id,
                            'subject': subject.name,
                            'requester_id': self.user.id
                        }
                    )
        else:
            await self.send(text_data=json.dumps({
                'type': 'added_to_queue',
                "subject": subject.name
            }))

    async def opponent_match_found(self, event):
        if event['opponent_id'] == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'match_found',
                'match_id': event['match_id'],
                'subject': event['subject']
            }))

    async def match_found(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_subject(self, subject_id):
        try:
            return Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return None

    @database_sync_to_async
    def get_user(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def create_match(self, subject):
        try:
            settings = PvpSettings.objects.filter(is_active=True).first()
            match = Match.objects.create(
                subject=subject,
                duration_minutes=settings.duration_minutes if settings else 15,
                max_tasks=settings.max_tasks if settings else 5
            )
            return match
        except Exception:
            return None

    @database_sync_to_async
    def add_participant(self, match, user):
        participant_count = MatchParticipant.objects.filter(match=match).count()
        return MatchParticipant.objects.create(
            match=match,
            user=user,
            player_number=participant_count + 1
        )

    @database_sync_to_async
    def generate_match_tasks(self, match):
        tasks = Task.objects.filter(topic__subject=match.subject).order_by('?')[:match.max_tasks]
        for i, task in enumerate(tasks, 1):
            MatchTask.objects.create(match=match, task=task, order=i)