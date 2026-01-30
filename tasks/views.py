from rest_framework import generics, permissions
from rest_framework.serializers import BooleanField
from rest_framework.views import APIView, Response
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404

from .models import Task, Subject, Topic
from .serializers import TaskSerializer, CheckAnswerSerializer, SubjectSerializer, TopicSerializer, TipSerializer

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes, OpenApiExample


@extend_schema_view(
    get=extend_schema(
        summary="Получение списка задач",
        description="Получение списка задач с возможностью фильтрации по имени и уровню сложности",
        parameters=[
            OpenApiParameter(
                name='name',
                location=OpenApiParameter.QUERY,
                description='фильтр задач по имени',
                required=False,
                type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name='difficulty_level',
                location=OpenApiParameter.QUERY,
                description='фильтр задач по уровню сложности',
                required=False,
                type=OpenApiTypes.STR,
                enum=['Easy', 'Medium', 'Hard']
            ),
            OpenApiParameter(
                name='page',
                location=OpenApiParameter.QUERY,
                description='Номер страницы',
                required=False,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="topic_id",
                location=OpenApiParameter.QUERY,
                description="ID темы",
                required=False,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name="subject_id",
                location=OpenApiParameter.QUERY,
                description="ID предмета",
                required=False,
                type=OpenApiTypes.INT
            )
        ],
        responses={
            200: TaskSerializer(many=True),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    ),
)
class TasksView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        name = self.request.query_params.get('name')
        difficulty_level = self.request.query_params.get('difficulty_level')
        topic_id = self.request.query_params.get('topic_id')
        subject_id = self.request.query_params.get('subject_id')

        if subject_id:
            subject = get_object_or_404(Subject, pk=subject_id)
            queryset = queryset.filter(topic__subject=subject)

        if topic_id:
            topic = get_object_or_404(Topic, pk=topic_id)
            queryset = queryset.filter(topic=topic)

        if name:
            queryset = queryset.filter(name__icontains=name)
        
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)

        ordering = getattr(self.get_serializer_class(), "ordering", None)
        return queryset.order_by(*ordering) if ordering else queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Получение задачи",
        description="Получение задачи по id",
        responses={
            200: TaskSerializer(),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    ),
    post=extend_schema(
        summary="Проверка ответа",
        description="Проверка ответа на задачу",
        request=CheckAnswerSerializer(),
        responses={
            200: OpenApiResponse(
                Response({
                    "is_correct": BooleanField()
                }), examples=[
                    OpenApiExample(name="Успешно", value={
                        "is_correct": True
                    })
                ]
            ),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    )
)
class TaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = self.serializer_class(task, context={'request': request})
        return Response(serializer.data)
    
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = CheckAnswerSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.check(task, request.data['answer'])
            if is_correct:
                request.user.solved_tasks.add(task)
                request.user.save()
            return Response({
                "is_correct": is_correct
            })
        else:
            return Response(serializer.errors, status=400)


@extend_schema_view(
    get=extend_schema(
        summary="Получение подсказки",
        description="Получение подсказки по id",
        responses={
            200: TipSerializer(),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    )
)
class TipView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TipSerializer

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = self.serializer_class(task, context={'request': request})
        return Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        summary="Получение учебных предметов",
        description="Получение учебных предметов",
        responses={
            200: TopicSerializer(many=True),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    )
)
class SubjectsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubjectSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Subject.objects.all()
        ordering = getattr(self.get_serializer_class(), "ordering", None)
        return qs.order_by(*ordering) if ordering else qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)



@extend_schema_view(
    get=extend_schema(
        summary="Получение тем учебного предмета",
        description="Получение тем учебного предмета",
        responses={
            200: TopicSerializer(many=True),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Tasks"]
    )
)
class TopicsView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TopicSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Topic.objects.filter(subject=self.kwargs["subject_id"])
        ordering = getattr(self.get_serializer_class(), "ordering", None)
        return qs.order_by(*ordering) if ordering else qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
