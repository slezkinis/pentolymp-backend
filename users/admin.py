from django.contrib import admin

from .models import User, Rating


class RatingInline(admin.StackedInline):
    model = Rating
    can_delete = False
    verbose_name_plural = 'Рейтинг'


class UserView(admin.ModelAdmin):
    list_display = ('username', 'email', 'get_rating_score', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    inlines = [RatingInline]
    
    def get_rating_score(self, obj):
        try:
            return obj.rating.score
        except Rating.DoesNotExist:
            return 0
    get_rating_score.short_description = 'Рейтинг'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


admin.site.register(User, UserView)