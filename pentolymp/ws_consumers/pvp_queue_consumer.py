import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from pvp.services import MatchScheduler
from pvp.models import Queue
from tasks.models import Subject


User = get_user_model()

class PvpQueueConsumer(AsyncWebsocketConsumer):
    _scheduler = MatchScheduler()

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
                await self.add_to_queue(subject_id)
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
    def delete_queue_entries(self, user_ids):
        try:
            Queue.objects.filter(user_id__in=user_ids).delete()
            return True
        except Exception:
            return False

    async def add_to_queue(self, subject_id):
        subject = await self.get_subject(subject_id)
        if not subject:
            raise Exception("Subject not found")
        
        queue_entry = await self.create_queue_entry(subject)
        if not queue_entry:
            raise Exception("Failed to create queue entry")
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
