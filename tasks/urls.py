from django.urls import path

from . import views

urlpatterns = [
    path("", views.TasksView.as_view(), name="tasks"),
    path("<int:pk>/", views.TaskView.as_view(), name="task"),
]