import csv
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from .forms import CsvImportForm
from .models import Task, Subject, Topic


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic', 'difficulty_level')
    list_filter = ('topic', 'difficulty_level')
    search_fields = ('name', 'description')
    change_list_template = 'admin/tasks_task_change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='tasks_task_import_csv'),
        ]
        return custom_urls + urls
    
    def import_csv(self, request):
        if request.method == 'POST':
            form = CsvImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Файл должен быть в формате CSV')
                    return redirect(request.path)
                
                try:
                    decoded_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)
                    
                    created_count = 0
                    error_count = 0
                    
                    for row in reader:
                        try:
                            subject, _ = Subject.objects.get_or_create(
                                name=row.get('subject', '').strip()
                            )
                            topic, _ = Topic.objects.get_or_create(
                                name=row.get('topic', '').strip(),
                                defaults={'subject': subject}
                            )
                            
                            Task.objects.create(
                                name=row.get('name', '').strip(),
                                description=row.get('description', '').strip(),
                                answer=row.get('answer', '').strip(),
                                topic=topic,
                                difficulty_level=row.get('difficulty_level', 'Medium').strip(),
                                tip=row.get('tip', '').strip() or None
                            )
                            created_count += 1
                        except Exception as e:
                            error_count += 1
                            continue
                    
                    if created_count > 0:
                        messages.success(request, f'Успешно создано {created_count} задач')
                    if error_count > 0:
                        messages.warning(request, f'Не удалось создать {error_count} задач')
                    
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {str(e)}')
                
                return redirect('admin:tasks_task_changelist')
        else:
            form = CsvImportForm()
        
        context = {
            'form': form,
            'opts': self.model._meta,
            'title': 'Импорт задач из CSV',
        }
        return render(request, 'admin/csv_import.html', context)
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context)


admin.site.register(Subject)
admin.site.register(Topic)