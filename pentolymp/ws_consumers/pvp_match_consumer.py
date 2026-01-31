import json
from datetime import timedelta

from asgiref.sync import sync_to_async, async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone

from pvp.models import Match, MatchParticipant, MatchTask, MatchStatus, MatchResult
from pvp.services import MatchScheduler
from users.models import Rating


User = get_user_model()


class PvpMatchConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.match_group = f"match_{self.match_id}"
        
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return
        
        await self.channel_layer.group_add(
            self.match_group,
            self.channel_name
        )
        await self.accept()
        
        await self.send_match_state()

    async def disconnect(self, close_code):
        await self.handle_disconnect()
        
        await self.channel_layer.group_discard(
            self.match_group,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'submit_answer':
            await self.submit_answer(data.get('answer'))
        elif message_type == 'ready':
            await self.player_ready()
        elif message_type == 'get_task':
            await self.send_current_task()
        elif message_type == 'get_match_state':
            await self.send_match_state()
        elif message_type == 'get_opponent_progress':
            await self.send_opponent_progress()
        elif message_type == 'get_my_progress':
            await self.send_my_progress()
        elif message_type == 'get_time_remaining':
            await self.send_time_remaining()

    async def send_match_state(self):
        match_data = await self.get_match_data()
        await self.send(text_data=json.dumps({
            'type': 'match_state',
            'match': match_data
        }))

    async def submit_answer(self, answer):
        """Отправить ответ на задачу"""
        if not answer:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Ответ не может быть пустым'
            }))
            return
        
        result = await self.check_answer(answer)
        
        await self.channel_layer.group_send(
            self.match_group,
            {
                'type': 'answer_submitted',
                'user_id': self.user.id,
                'username': self.user.username,
                'correct': result['correct'],
                'task_id': result['task_id'],
                'task_order': result['task_order'],
            }
        )
        
        if result['correct']:
            await self.set_task_solved(result['task_id'])
            await self.update_progress(result['task_id'])
            is_complete, data = await self.check_match_complete()
            if is_complete:
                await self.channel_layer.group_send(
                    self.match_group,
                    data
                )
                return
            
            next_task = await self.get_next_task()
            if next_task:
                await self.send(text_data=json.dumps({
                    'type': 'next_task',
                    'data': next_task
                }))
            else:
                is_complete, data = await self.check_match_complete()
                if is_complete:
                    await self.channel_layer.group_send(
                        self.match_group,
                        data
                    )
                    return

    async def player_ready(self):
        await self.set_player_ready()
        await self.channel_layer.group_send(
            self.match_group,
            {
                'type': 'player_ready_update',
                'user_id': self.user.id
            }
        )
        is_started = await self.check_start_match()
        if is_started:
            await self.channel_layer.group_send(
                self.match_group,
                {
                    'type': 'match_started',
                    "end_at": await self.get_match_end_time()
                }
            )

    async def send_current_task(self):
        task_data = await self.get_current_task()
        await self.send(text_data=json.dumps({
            'type': 'current_task',
            'task': task_data
        }))

    async def answer_submitted(self, event):
        """Обработка отправленного ответа"""
        if event['user_id'] == self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'own_answer_result',
                'data': {
                    'correct': event['correct'],
                    'task_id': event['task_id'],
                    'task_order': event['task_order'],
                }
            }))
        else:
            await self.send(text_data=json.dumps({
                'type': 'opponent_answer',
                'data': {
                    'user_id': event['user_id'],
                    'username': event.get('username', 'Opponent'),
                    'correct': event['correct'],
                    'task_order': event['task_order'],
                }
            }))

    async def player_ready_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_ready',
            'user_id': event['user_id']
        }))

    async def handle_disconnect(self):
        status = await self.set_technical_result()
        if status:
            await self.channel_layer.group_send(
                self.match_group,
                {
                        'type': 'match_finished',
                        'result': "technical",
                        'winner': None,
                        'participants': [
                        ]
                    }
            )

    @database_sync_to_async
    def check_participant(self):
        try:
            return MatchParticipant.objects.filter(
                match_id=self.match_id,
                user=self.user
            ).exists()
        except:
            return False

    @database_sync_to_async
    def set_task_solved(self, task_id):
        try:
            user = User.objects.get(id=self.user.id)
            user.solved_tasks.add(task_id)
            user.save()
            return True
        except Exception as e:
            print(e)
            return False

    @database_sync_to_async
    def get_match_data(self):
        try:
            match = Match.objects.get(id=self.match_id)
            participants = match.participants.all()
            
            return {
                'id': match.id,
                'subject': match.subject.name,
                'status': match.status,
                'duration_minutes': match.duration_minutes,
                'max_tasks': match.max_tasks,
                'participants': [
                    {
                        'user_id': p.user.id,
                        'username': p.user.username,
                        'player_number': p.player_number,
                        'tasks_solved': p.tasks_solved,
                        'current_task_index': p.current_task_index
                    }
                    for p in participants
                ]
            }
        except Match.DoesNotExist:
            return None

    @database_sync_to_async
    def get_current_task(self):
        try:
            participant = MatchParticipant.objects.get(match_id=self.match_id, user=self.user)
            match_task = MatchTask.objects.filter(
                match_id=self.match_id,
                order=participant.current_task_index + 1
            ).first()
            
            if match_task:
                return {
                    'id': match_task.task.id,
                    'name': match_task.task.name,
                    'description': match_task.task.description,
                    'order': match_task.order
                }
            return None
        except:
            return None

    @database_sync_to_async
    def get_next_task(self):
        try:
            participant = MatchParticipant.objects.get(match_id=self.match_id, user=self.user)
            match_task = MatchTask.objects.filter(
                match_id=self.match_id,
                order=participant.current_task_index + 1
            ).first()
            
            if match_task:
                return {
                    'id': match_task.task.id,
                    'name': match_task.task.name,
                    'description': match_task.task.description,
                    'order': match_task.order
                }
            return None
        except:
            return None

    @database_sync_to_async
    def check_answer(self, answer):
        try:
            participant = MatchParticipant.objects.get(match_id=self.match_id, user=self.user)
            match_task = MatchTask.objects.filter(
                match_id=self.match_id,
                order=participant.current_task_index + 1
            ).first()

            match = Match.objects.get(id=self.match_id)
            if match.status != MatchStatus.PLAYING:
                return {'correct': False, 'task_id': match_task.task.id, 'task_order': match_task.order}
            
            if match_task:
                is_correct = match_task.task.check_answer(answer)
                return {
                    'correct': is_correct,
                    'task_id': match_task.task.id,
                    'task_order': match_task.order,
                }
            return {'correct': False, 'task_id': None, 'task_order': None}
        except:
            return {'correct': False, 'task_id': None, 'task_order': None}

    @database_sync_to_async
    def update_progress(self, task_id):
        try:
            participant = MatchParticipant.objects.get(match_id=self.match_id, user=self.user)
            participant.tasks_solved += 1
            participant.current_task_index += 1
            participant.save()
            return True
        except:
            return False

    @database_sync_to_async
    def set_player_ready(self):
        try:
            MatchParticipant.objects.get(match_id=self.match_id, user=self.user)
            return True
        except:
            return False

    @database_sync_to_async
    def set_technical_result(self):
        try:
            match = Match.objects.get(id=self.match_id)
            if match.status != MatchStatus.PLAYING:
                return False
            match.status = MatchStatus.TECHNICAL_ERROR
            match.result = MatchResult.TECHNICAL
            match.finished_at = timezone.now()
            match.save()
            
            participants = match.participants.all()
            for participant in participants:
                Rating.objects.get_or_create(user=participant.user)[0]
            return True
        except:
            return False

    @database_sync_to_async
    def check_start_match(self):
        try:
            match = Match.objects.get(id=self.match_id)
            participants = match.participants.all()
            
            if len(participants) == 2 and match.status == MatchStatus.WAITING:
                match.status = MatchStatus.PLAYING
                match.started_at = timezone.now()
                match.save()

                scheduler = MatchScheduler()
                scheduler.schedule_match_finish(self.match_id, match.duration_minutes, self.finish_match_timeout)
                return True
            return False
        except:
            return False

    async def match_started(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_started',
            "end_at": event['end_at']
        }))

    @database_sync_to_async
    def get_match_end_time(self):
        try:
            match = Match.objects.get(id=self.match_id)
            return (match.started_at + timedelta(minutes=match.duration_minutes)).isoformat()
        except:
            return None
        
    def finish_match_timeout(self):
        is_completed, data = async_to_sync(self.check_match_complete)(time_expired=True)
        if is_completed:
            async_to_sync(self.channel_layer.group_send)(
                self.match_group,
                data
            )
            return

    @database_sync_to_async
    def check_match_complete(self, time_expired=False, match_id=None):
        try:
            match = Match.objects.get(id=self.match_id)
            participants = list(match.participants.all())
            
            all_complete = any(p.tasks_solved == match.match_tasks.count() for p in participants)
            
            if all_complete or time_expired:
                if participants[0].tasks_solved > participants[1].tasks_solved:
                    result = MatchResult.PLAYER1_WIN
                    winner = participants[0].user
                elif participants[1].tasks_solved > participants[0].tasks_solved:
                    result = MatchResult.PLAYER2_WIN
                    winner = participants[1].user
                else:
                    result = MatchResult.DRAW
                
                match.status = MatchStatus.FINISHED
                match.result = result
                match.winner = winner if result != MatchResult.DRAW else None
                match.finished_at = timezone.now()
                match.save()
                
                if not time_expired:
                    scheduler = MatchScheduler()
                    scheduler.cancel_match_schedule(self.match_id)
                self.update_ratings(participants, result)

                for p in participants:
                    p.time_taken += (timezone.now() - match.started_at).seconds
                    p.save()

                return (True, {
                        'type': 'match_finished',
                        'result': result,
                        'winner': {
                            'user_id': winner.id,
                            'username': winner.username
                        } if result != MatchResult.DRAW else None,
                        'participants': [
                            {
                                'user_id': p.user.id,
                                'username': p.user.username,
                                'tasks_solved': p.tasks_solved,
                                'time_taken': p.time_taken
                            }
                            for p in participants
                        ]
                    }
                )
                
            return (False, {})
        except Exception as e:
            print(e)
            return (False, {})

    def update_ratings(self, participants, result):
        from pvp.services import RatingService
        RatingService.update_match_ratings(self.match_id)

    async def match_finished(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_finished',
            'result': event['result'],
            'participants': event['participants'],
            'winner': event['winner']
        }))

    async def send_opponent_progress(self):
        """Отправить прогресс оппонента"""
        try:
            @sync_to_async
            def get_opponent_data():
                match = Match.objects.get(id=self.match_id)
                opponent = match.participants.select_related('user').exclude(
                    user__id=self.user.id
                ).first()
                
                if opponent:
                    return {
                        'tasks_solved': opponent.tasks_solved,
                        'current_task_index': opponent.current_task_index,
                        'time_taken': opponent.time_taken
                    }
                return None
            
            opponent_data = await get_opponent_data()
            
            if opponent_data:
                await self.send(text_data=json.dumps({
                    'type': 'opponent_progress',
                    'data': opponent_data
                }))
        except Exception as e:
            print(f"Error in send_opponent_progress: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка получения прогресса оппонента: {e}'
            }))

    async def send_my_progress(self):
        """Отправить свой прогресс"""
        try:
            @sync_to_async
            def get_my_data():
                match = Match.objects.get(id=self.match_id)
                my = match.participants.select_related('user').filter(
                    user__id=self.user.id
                ).first()
                
                if my:
                    return {
                        'tasks_solved': my.tasks_solved,
                        'current_task_index': my.current_task_index,
                        'time_taken': my.time_taken
                    }
                return None
            
            my_data = await get_my_data()
            
            if my_data:
                await self.send(text_data=json.dumps({
                    'type': 'my_progress',
                    'data': my_data
                }))
        except Exception as e:
            print(f"Error in send_my_progress: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка получения своего прогресса: {e}'
            }))

    async def send_time_remaining(self):
        """Отправить оставшееся время"""
        try:
            match = await database_sync_to_async(Match.objects.get)(id=self.match_id)
            
            if match.status != 'playing' or not match.started_at:
                await self.send(text_data=json.dumps({
                    'type': 'time_remaining',
                    'data': {'seconds': None}
                }))
                return
            
            now = timezone.now()
            elapsed = (now - match.started_at).total_seconds()
            total_seconds = match.duration_minutes * 60
            remaining = max(0, total_seconds - elapsed)
            
            await self.send(text_data=json.dumps({
                'type': 'time_remaining',
                'data': {
                    'seconds': int(remaining),
                    'elapsed': int(elapsed),
                    'total': total_seconds
                }
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка получения времени: {e}'
            }))