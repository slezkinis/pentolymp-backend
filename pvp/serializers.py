from rest_framework import serializers
from .models import Match, MatchParticipant, MatchTask, PvpSettings
from tasks.models import Subject, Task
from users.models import Rating
from users.serializers import UserSerializer


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'difficulty_level']


class MatchTaskSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    
    class Meta:
        model = MatchTask
        fields = ['task', 'order']


class MatchParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MatchParticipant
        fields = ['user', 'player_number', 'tasks_solved', 'time_taken', 'current_task_index']


class MatchSerializer(serializers.ModelSerializer):
    participants = MatchParticipantSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True)
    match_tasks = MatchTaskSerializer(many=True, read_only=True)
    
    class Meta:
        model = Match
        fields = [
            'id', 'subject', 'status', 'result', 'created_at', 'started_at', 'finished_at',
            'duration_minutes', 'max_tasks', 'participants', 'match_tasks'
        ]


class CreateMatchSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    duration_minutes = serializers.IntegerField(required=False, min_value=5, max_value=60)
    max_tasks = serializers.IntegerField(required=False, min_value=3, max_value=20)


class PvpSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PvpSettings
        fields = ['name', 'duration_minutes', 'max_tasks', 'k_factor', 'initial_rating', 'is_active']


class RatingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = ['user', 'score', 'matches_played', 'matches_won', 'matches_lost', 'matches_drawn']


class LeaderboardSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    user = UserSerializer()
    rating = serializers.IntegerField()
    matches_played = serializers.IntegerField()
    win_rate = serializers.FloatField()