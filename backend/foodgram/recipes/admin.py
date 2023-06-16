from django.contrib import admin
from .models import Recipe, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'name')
    list_filter = ('author', 'name')
    empty_value_display = '-пусто-'


admin.site.register(Tag)
