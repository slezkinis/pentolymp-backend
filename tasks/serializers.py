import rest_framework.serializers as serializers

from .models import Task, Topic, Subject


class TaskSerializer(serializers.ModelSerializer):
    is_solved = serializers.BooleanField()
    topic = serializers.CharField(source='topic.name')
    subject = serializers.CharField(source='topic.subject.name')
    ordering = ["id"]

    class Meta:
        model = Task
        fields = ['id', 'name', 'description', 'difficulty_level', 'is_solved', 'topic', "subject"]
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['is_solved'] = instance.is_solved(self.context['request'].user)
        return representation
    
    def check_answer(self, answer):
        return self.instance.check_answer(answer)


class CheckAnswerSerializer(serializers.Serializer):
    answer = serializers.CharField(required=True)

    def check(self, task, answer):
        return task.check_answer(answer)


class TopicSerializer(serializers.ModelSerializer):
    ordering = ["name"]

    class Meta:
        model = Topic
        fields = ['id', 'name']


class SubjectSerializer(serializers.ModelSerializer):
    ordering = ["name"]

    class Meta:
        model = Subject
        fields = ['id', 'name']


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'tip']


class SubjectStatisticSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    tasks_solved = serializers.IntegerField()
    tasks_total = serializers.IntegerField()
    percentage = serializers.FloatField()

    class Meta:
        model = Subject
        fields = ["name", "tasks_solved", "tasks_total", "percentage"]
    
    def get_percentage(self, obj):
        if hasattr(obj, 'percentage'):
            return round(obj.percentage, 2)
        if obj.tasks_total > 0:
            return round((obj.tasks_solved / obj.tasks_total) * 100, 2)
        return 0.0