import os
import csv

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные об ингредиентах из CSV-файла в базу данных'

    def handle(self, *args, **options):
        file_path = os.path.join(
            settings.BASE_DIR, 'foodgram', 'static', 'data', 'ingredients.csv'
        )

        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for name, measurement_unit in reader:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit
                )
                if created:
                    print(f'Создан ингредиент "{name}".')
                else:
                    print(f'Ингредиент "{name}" уже существует. Создание пропущено.')

        self.stdout.write(self.style.SUCCESS('Данные успешно загружены в базу данных.'))
