from django.contrib import admin

from .models import User


@admin.register(User)
class RecipesUser(admin.ModelAdmin):
    list_display = 'username'
    list_filter = ('email', 'username',)
    empty_value_display = '-пусто-'
