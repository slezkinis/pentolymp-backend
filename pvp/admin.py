import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.utils import timezone

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
    change_list_template = 'admin/pvp_match_change_list.html'
    
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
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-csv/', self.admin_site.admin_view(self.export_csv), name='pvp_match_export_csv'),
        ]
        return custom_urls + urls
    
    def export_csv(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="matches_statistics" {timezone.now().strftime("%Y-%m-%d")}.csv'
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID матча', 'Предмет', 'Статус', 'Результат', 'Победитель',
            'Дата создания', 'Дата начала', 'Дата окончания', 'Длительность (мин)',
            'Макс. задач', 'Игрок 1', 'Игрок 2',
            'Решено задач (Игрок 1)', 'Решено задач (Игрок 2)',
            'Время (Игрок 1, сек)', 'Время (Игрок 2, сек)'
        ])
        
        matches = Match.objects.all().select_related('subject', 'winner').prefetch_related('participants__user')
        
        for match in matches:
            participants = list(match.participants.all())
            player1 = participants[0] if len(participants) > 0 else None
            player2 = participants[1] if len(participants) > 1 else None
            
            writer.writerow([
                match.id,
                match.subject.name,
                match.get_status_display(),
                match.get_result_display() if match.result else '',
                match.winner.username if match.winner else '',
                match.created_at.strftime('%Y-%m-%d %H:%M:%S') if match.created_at else '',
                match.started_at.strftime('%Y-%m-%d %H:%M:%S') if match.started_at else '',
                match.finished_at.strftime('%Y-%m-%d %H:%M:%S') if match.finished_at else '',
                match.duration_minutes,
                match.max_tasks,
                player1.user.username if player1 else '',
                player2.user.username if player2 else '',
                player1.tasks_solved if player1 else '',
                player2.tasks_solved if player2 else '',
                player1.time_taken if player1 else '',
                player2.time_taken if player2 else '',
            ])
        
        return response


@admin.register(PvpSettings)
class PvpSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes', 'max_tasks', 'max_rating_diff_for_nodelay', 'min_wait_time', 'is_active']
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
        }),
        ('Настройки задержек', {
            'fields': ('max_rating_diff_for_nodelay', 'min_wait_time')
        })
    )
