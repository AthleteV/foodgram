import csv

from django.core.management import BaseCommand
from django.db import IntegrityError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузить ингредиенты из CSV-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к CSV-файлу',
            default='data/ingredients.csv'
        )

    def handle(self, *args, **kwargs):
        path = kwargs['path']
        added_count = 0

        with open(path, 'rt', encoding='utf-8') as file:
            reader = csv.reader(file, dialect='excel')
            ingredients_to_create = [
                (row[0], row[1])
                for row in reader if row[0]
            ]

            for name, measurement_unit in ingredients_to_create:
                if not Ingredient.objects.filter(name=name).exists():
                    try:
                        Ingredient.objects.create(
                            name=name, measurement_unit=measurement_unit)
                        added_count += 1
                    except IntegrityError:
                        self.stdout.write(self.style.WARNING(
                            f'Ошибка при добавлении ингредиента {name}.'
                        ))

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно загружено {added_count} уникальных ингредиентов.'
            )
        )
