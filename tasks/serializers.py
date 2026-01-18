from rest_framework.serializers import ModelSerializer, BooleanField

from .models import Task


class TaskSerializer(ModelSerializer):
    is_solved = BooleanField()
    class Meta:
        model = Task
        fields = 'id', 'name', 'description', 'difficulty_level', 'is_solved'
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_solved'] = instance.is_solved(self.context['request'].user)
        return representation


class AnswerSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = 'answer'
    