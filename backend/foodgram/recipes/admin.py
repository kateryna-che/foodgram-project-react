from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag, TagRecipe)


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorite',
                    'display_ingredients', 'display_tags', 'display_image')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    inlines = [IngredientRecipeInline]

    @admin.display(description='Добавлен в избранное')
    def in_favorite(self, obj):
        return obj.favorites.count()

    @admin.display(description='Ингредиенты')
    def display_ingredients(self, obj):
        return ', '.join(obj.ingredients.values_list('name', flat=True))

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True))

    @admin.display(description='Изображение')
    def display_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60">'
            )
        else:
            return 'No Image'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
