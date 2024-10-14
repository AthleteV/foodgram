import csv

from django.core.management import BaseCommand
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

        with open(path, 'rt', encoding='utf-8') as file:
            reader = csv.reader(file, dialect='excel')
            ingredients_to_create = [
                Ingredient(name=row[0], measurement_unit=row[1])
                for row in reader if row[0]
            ]
            Ingredient.objects.bulk_create(ingredients_to_create)

        self.stdout.write(
            self.style.SUCCESS(
                f'Успешно загружено {len(ingredients_to_create)} ингредиентов.'
            )
        )
