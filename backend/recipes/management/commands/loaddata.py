import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from recipes.models import Tag


class Command(BaseCommand):
    help = (
        'Автоматическая загрузка данных, создание суперпользователя и '
        'добавление предопределённых тегов'
    )

    def handle(self, *args, **options):
        # Получение параметров суперпользователя из .env
        admin_username = os.getenv('ADMIN_USERNAME')
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')

        if not all([admin_username, admin_email, admin_password]):
            self.stdout.write(
                self.style.ERROR(
                    'Параметры суперпользователя не заданы в .env')
            )
            return

        # Применение миграций
        call_command('makemigrations')
        call_command('migrate', '--noinput')

        # Проверка заполненности базы данных
        User = get_user_model()
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    'Данные уже существуют в базе данных. Пропуск загрузки.'
                )
            )
        else:
            # Загрузка данных из CSV
            self.stdout.write('Загрузка данных из CSV...')
            call_command('loadcsv')

            # Создание суперпользователя
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

            # Добавление предопределённых тегов
            self.stdout.write('Добавление предопределённых тегов...')
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

        # Сборка статики
        call_command('collectstatic', '--noinput')
        self.stdout.write(self.style.SUCCESS('Статика успешно собрана.'))
