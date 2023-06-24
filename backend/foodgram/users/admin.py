from django.contrib import admin
from django.contrib.auth.models import Group

from recipes.models import Recipe

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'recipe_count', 'follower_count')
    list_filter = ('email', 'username',)
    empty_value_display = '-пусто-'

    def recipe_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def follower_count(self, obj):
        return Subscription.objects.filter(author=obj).count()

    recipe_count.short_description = 'Количество рецептов'
    follower_count.short_description = 'Количество подписчиков'


admin.site.register(Subscription)
admin.site.unregister(Group)
