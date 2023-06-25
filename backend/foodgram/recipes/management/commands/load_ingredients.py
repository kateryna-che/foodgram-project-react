import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные об ингредиентах из CSV-файла в базу данных'

    # используя двойные обратные слеши \\
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str,
                            help='Абсолютный путь к CSV-файлу')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)
            for name, measurement_unit in reader:
                ingredient, created = Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit
                )
                if created:
                    print(f'Создан ингредиент "{name}".')
                else:
                    print(f'Ингредиент "{name}" уже существует.'
                          'Создание пропущено.')

        self.stdout.write(self.style.SUCCESS(
            'Данные успешно загружены в базу данных.'
        ))
