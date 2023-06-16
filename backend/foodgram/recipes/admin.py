from django.contrib import admin
from .models import Recipe


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'name')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'