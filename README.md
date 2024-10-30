# Foodgram

## Описание проекта

**Foodgram** — это веб-приложение, позволяющее пользователям делиться рецептами и создавать списки покупок. Приложение обеспечивает удобный интерфейс для поиска рецептов, сохранения избранных блюд и взаимодействия с другими пользователями.

## Ссылка на веб-приложение

[foodv.ddns.net](http://foodv.ddns.net)

## Технологический стек

- **Python** — основной язык программирования.
- **Django** — фреймворк для веб-приложений.
- **PostgreSQL** — система управления данными.
- **Nginx** — веб-сервер для обработки запросов.
- **Docker** — платформа для разработки, доставки и запуска контейнерных приложений.
- **Git** — система управления версиями с распределенной архитектурой.

## Сборка проекта

Создайте файл `.env` в корневой директории проекта и добавьте следующие параметры:

POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

SECRET_KEY=<django_secret_key>
ALLOWED_HOSTS=example.net,123.123.123.123
DEBUG=False

ADMIN_USERNAME=admin
ADMIN_EMAIL=<admin_mail@mail.ru>
ADMIN_PASSWORD=admin_password

Находясь в папке `infra`, выполните команду `docker compose up`.
db: будет создан контейнер PostgreSQL

backend: Django-бэкенд будет собран из директории `../backend`. Команда `python manage.py setup_all && gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000`
загрузит данные из CSV, создаст теги, создаст суперпользователя, запустит миграции, соберет статику и запустит сервер Gunicorn для Django.

frontend: фронтенд будет собран из директории `../frontend`, и команда `cp -r /app/build/. /static/` скопирует статические файлы из фронтенд-приложения в volume

nginx: после запуска frontend и backend контейнер Nginx будет использовать static и media volume для сервировки статических и медиафайлов, а также будет перенаправлять запросы к бэкенду, предоставляя API на порту 8000.

По адресу [http://localhost:8000](http://localhost:8000) находится веб-приложение, а по адресу [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/) — спецификация API.

## Автор

Проект разработан [AthleteV](https://github.com/AthleteV)
