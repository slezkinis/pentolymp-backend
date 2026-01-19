from rest_framework.serializers import ModelSerializer, BooleanField, CharField, ValidationError, Serializer

from .models import Task, Topic, Subject


class TaskSerializer(ModelSerializer):
    is_solved = BooleanField()
    topic = CharField(source='topic.name')
    subject = CharField(source='topic.subject.name')
    class Meta:
        model = Task
        fields = 'id', 'name', 'description', 'difficulty_level', 'is_solved', 'topic', "subject"
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_solved'] = instance.is_solved(self.context['request'].user)
        return representation
    
    def check_answer(self, answer):
        return self.instance.check_answer(answer)


class CheckAnswerSerializer(Serializer):
    answer = CharField(required=True)

    def check(self, task, answer):
        return task.check_answer(answer)


class TopicSerializer(ModelSerializer):
    class Meta:
        model = Topic
        fields = 'id', 'name'


class SubjectSerializer(ModelSerializer):
    class Meta:
        model = Subject
        fields = 'id', 'name'


class TipSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = 'id', 'tip'