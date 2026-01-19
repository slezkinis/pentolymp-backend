from django.contrib import admin

from .models import Task, Subject, Topic

admin.site.register(Task)
admin.site.register(Subject)
admin.site.register(Topic)