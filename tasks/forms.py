from django import forms


class CsvImportForm(forms.Form):
    csv_file = forms.FileField(
        label='CSV файл',
        help_text='Выберите CSV файл с задачами. Файл должен содержать колонки: name, description, answer, subject, topic, difficulty_level, tip'
    )
