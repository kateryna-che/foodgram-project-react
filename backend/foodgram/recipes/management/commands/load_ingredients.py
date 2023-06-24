import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные об ингредиентах из CSV-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str,
                            help='Абсолютный путь к CSV-файлу')  # используя двойные обратные слеши \\

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                name, measurement_unit = row[:2]
                ingredients = Ingredient.objects.filter(name=name)
                if ingredients.exists():
                    print(
                        f'Ингредиент "{name}" уже существует. Создание пропущено.'
                    )
                else:
                    Ingredient.objects.create(name=name,
                                              measurement_unit=measurement_unit)
                    print(f'Создан ингредиент "{name}".')

        self.stdout.write(self.style.SUCCESS(
            'Данные успешно загружены в базу данных.'
        ))
