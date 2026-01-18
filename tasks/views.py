from rest_framework import generics, permissions
from rest_framework.views import APIView, Response, status
from rest_framework.pagination import PageNumberPagination

from django.shortcuts import get_object_or_404

from .models import Task
from .serializers import TaskSerializer

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiResponse, OpenApiParameter, OpenApiTypes


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

        if name:
            queryset = queryset.filter(name__icontains=name)
        
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)
        
        return queryset
    
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
    )
)
class TaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = self.serializer_class(task, context={'request': request})
        return Response(serializer.data)
