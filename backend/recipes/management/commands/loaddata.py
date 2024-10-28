import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from recipes.models import Tag


class Command(BaseCommand):
    help = (
        'Загрузка данных из CSV, создание суперпользователя и '
        'тегов, запуск миграций'
    )

    def handle(self, *args, **options):
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if not all([admin_username, admin_email, admin_password]):
            self.stdout.write(
                self.style.ERROR(
                    'Параметры суперпользователя не заданы в .env')
            )
            return

        call_command('makemigrations')
        call_command('migrate', '--noinput')

        User = get_user_model()
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Данные уже существуют в базе данных. Пропуск загрузки.'
                )
            )
        else:
            self.stdout.write('Загрузка данных из CSV...')
            call_command('loadcsv')

            self.stdout.write('Создание суперпользователя...')
            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_superuser(
                    admin_username, admin_email, admin_password
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Суперпользователь {admin_username} создан.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Суперпользователь {admin_username} уже существует.'
                    )
                )

            self.stdout.write('Создание тегов...')
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
                            f'Тег "{tag_data["name"]}" успешно создан.')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Тег "{tag_data["name"]}" уже существует.')
                    )

        call_command('collectstatic', '--noinput')
        self.stdout.write(self.style.SUCCESS('Статика успешно собрана.'))
