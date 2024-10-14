import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = (
        'Запуск миграций, загрузка данных из CSV, создание тегов '
        'и запуск сервера.'
    )

    def handle(self, *args, **kwargs):
        if os.environ.get('RUN_MAIN') != 'true':
            self.stdout.write(self.style.NOTICE('Создание миграций...'))
            call_command('makemigrations')
            self.stdout.write(
                self.style.SUCCESS('Миграции успешно созданы.')
            )

            self.stdout.write(self.style.NOTICE('Применение миграций...'))
            call_command('migrate')
            self.stdout.write(self.style.SUCCESS('Миграции применены.'))

            self.stdout.write(
                self.style.NOTICE('Загрузка данных из CSV...')
            )
            try:
                call_command('loadcsv')
                self.stdout.write(
                    self.style.SUCCESS('Данные из CSV успешно загружены.')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при загрузке данных из CSV: {e}')
                )

            self.stdout.write(
                self.style.NOTICE('Создание тегов...')
            )
            tags = [
                {'name': 'Завтрак', 'slug': 'breakfast'},
                {'name': 'Обед', 'slug': 'lunch'},
                {'name': 'Ужин', 'slug': 'dinner'},
            ]

            for tag_data in tags:
                tag, created = Tag.objects.get_or_create(**tag_data)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Тег '{tag.name}' успешно создан."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Тег '{tag.name}' уже существует."
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS('Настройка успешно завершена.')
            )
            self.stdout.write(self.style.NOTICE('Запуск сервера...'))

        call_command('runserver', '0.0.0.0:8000')
