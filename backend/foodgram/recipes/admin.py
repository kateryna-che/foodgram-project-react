from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag, TagRecipe)


class IngredientRecipeInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        ingredients_count = sum(1 for form in self.forms if form.cleaned_data
                                and not form.cleaned_data.get('DELETE'))
        if ingredients_count < 1:
            raise ValidationError(
                'Колличество ингредиентов должно быть больше 1.'
            )


class IngredientRecipeInline(admin.TabularInline):
    model = IngredientRecipe
    formset = IngredientRecipeInlineFormSet


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'in_favorite',
                    'display_ingredients', 'display_tags', 'display_image')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    inlines = [IngredientRecipeInline]

    def in_favorite(self, obj):
        return obj.favorites.count()

    def display_ingredients(self, obj):
        return ', '.join(obj.ingredients.values_list('name', flat=True))

    def display_tags(self, obj):
        return ', '.join(obj.tags.values_list('name', flat=True))

    def display_image(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="80" height="60">'
            )
        else:
            return 'No Image'

    in_favorite.short_description = 'Добавлен в избранное'
    display_ingredients.short_description = 'Ингредиенты'
    display_tags.short_description = 'Теги'
    display_image.short_description = 'Изображение'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Tag)
admin.site.register(IngredientRecipe)
admin.site.register(TagRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
