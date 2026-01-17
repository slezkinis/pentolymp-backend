from django.contrib import admin

from .models import User


class UserView(admin.ModelAdmin):
    pass


admin.site.register(User, UserView)