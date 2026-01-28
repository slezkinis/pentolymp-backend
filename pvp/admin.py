from django.contrib import admin
from .models import Match, MatchParticipant, MatchTask, PvpSettings, Queue


class MatchParticipantInline(admin.TabularInline):
    model = MatchParticipant
    extra = 0
    readonly_fields = ['connected_at', 'tasks_solved', 'time_taken', 'current_task_index']


class MatchTaskInline(admin.TabularInline):
    model = MatchTask
    extra = 0
    ordering = ['order']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'status', 'result', 'created_at', 'duration_minutes', 'max_tasks']
    list_filter = ['status', 'result', 'subject', 'created_at']
    search_fields = ['id', 'subject__name']
    readonly_fields = ['created_at', 'started_at', 'finished_at']
    inlines = [MatchParticipantInline, MatchTaskInline]
    
    fieldsets = (
        ('Основное', {
            'fields': ('subject', 'status', 'result')
        }),
        ('Настройки', {
            'fields': ('duration_minutes', 'max_tasks')
        }),
        ('Время', {
            'fields': ('created_at', 'started_at', 'finished_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(MatchParticipant)
class MatchParticipantAdmin(admin.ModelAdmin):
    list_display = ['user', 'match', 'player_number', 'tasks_solved', 'time_taken', 'connected_at']
    list_filter = ['player_number', 'connected_at', 'match__status']
    search_fields = ['user__username', 'user__email', 'match__id']
    readonly_fields = ['connected_at']


@admin.register(MatchTask)
class MatchTaskAdmin(admin.ModelAdmin):
    list_display = ['match', 'task', 'order']
    list_filter = ['match__subject', 'order']
    search_fields = ['match__id', 'task__name']


@admin.register(PvpSettings)
class PvpSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'max_tasks', 'k_factor', 'initial_rating', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'is_active')
        }),
        ('Настройки матча', {
            'fields': ('duration_minutes', 'max_tasks')
        }),
        ('Настройки рейтинга', {
            'fields': ('k_factor', 'initial_rating')
        })
    )


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['user', 'subject', 'created_at']
    list_filter = ['subject', 'created_at']
    search_fields = ['user__username', 'user__email', 'subject__name']
    readonly_fields = ['created_at']

