#!/bin/sh

# Применение миграций
python manage.py makemigrations
python manage.py migrate --noinput

# Проверка, заполнена ли база данных
if python manage.py shell -c "from django.contrib.auth import get_user_model; print(get_user_model().objects.exists())" | grep -q "True"; then
    echo "Данные уже существуют в базе данных. Пропуск загрузки данных."
else
    # Загрузка данных из CSV
    echo "Загрузка данных из CSV..."
    python manage.py loadcsv

    # Создание суперпользователя, если он ещё не создан
    echo "Создание суперпользователя..."
    echo "from django.contrib.auth import get_user_model; \
    User = get_user_model(); \
    User.objects.filter(username='$ADMIN_USERNAME').exists() or \
    User.objects.create_superuser('$ADMIN_USERNAME', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')" | python manage.py shell
    
    # Добавление тегов
    echo "Добавление предопределённых тегов..."
    python manage.py shell -c "
from recipes.models import Tag

tags = [
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
]

for tag_data in tags:
    tag, created = Tag.objects.get_or_create(**tag_data)
    if created:
        print(f'Тег \"{tag_data[\"name\"]}\" успешно создан.')
    else:
        print(f'Тег \"{tag_data[\"name\"]}\" уже существует.')
"
fi

# Сборка статики
python manage.py collectstatic --noinput
