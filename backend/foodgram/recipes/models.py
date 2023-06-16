from django.db import models

from users.models import User


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=200
    )
    image = models.ImageField(
    )
    text = models.TextField(
        'Текстовое описание',
    )
    ingredients = None
    tags = None
    cooking_time = models.PositiveIntegerField(
        'Время приготовления(в минутах)',
    )
