from django.urls import path

from . import views

urlpatterns = [
    path("tasks/", views.TasksView.as_view(), name="tasks"),
    path("tasks/<int:pk>/", views.TaskView.as_view(), name="task"),
    path("subjects/", views.SubjectsView.as_view(), name="subjects"),
    path("subjects/<int:subject_id>/topics/", views.TopicsView.as_view(), name="topics"),
]