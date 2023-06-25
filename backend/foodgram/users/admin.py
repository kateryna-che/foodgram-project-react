from django.contrib import admin
from django.contrib.auth.models import Group

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'recipe_count', 'follower_count')
    list_filter = ('email', 'username',)
    empty_value_display = '-пусто-'

    @admin.display(description='Количество рецептов')
    def recipe_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def follower_count(self, obj):
        return obj.following.count()


admin.site.register(Subscription)
admin.site.unregister(Group)
