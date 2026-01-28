from django.contrib import admin

from .models import User, Rating


class UserView(admin.ModelAdmin):
    pass


class RatingView(admin.ModelAdmin):
    pass

admin.site.register(User, UserView)
admin.site.register(Rating, RatingView)