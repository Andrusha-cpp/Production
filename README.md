# Production
Репозиторий проекта по Питону "Тотализатор Мисс РФиКТ"

## Локальный запуск
1. Установите зависимости (Python 3.12+):
   ```bash
   python -m venv .venv
   # macOS/Linux:
   source .venv/bin/activate
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Примените миграции:
   ```bash
   python manage.py migrate
   ```

3. Наполните базу демо-данными (опционально, фотографии подтянутся из `core/management/commands/media_seed` и положатся в `media/candidates`):
   ```bash
   python manage.py seed_candidates
   ```

4. Запустите сервер разработки:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

Приложение будет доступно на http://localhost:8000/

## Тесты
Запустите встроенные Django-тесты:
```bash
python manage.py test
```

В Docker:
```bash
# из корня проекта
docker-compose run --rm web python manage.py test
```

## Запуск в Docker
1. Соберите и запустите:
   ```bash
   docker-compose up --build
   ```
   Контейнер применит миграции и поднимет сервер на `http://localhost:8000/`.

2. Остановить:
   ```bash
   docker-compose down
   ```

3. Выполнить команду внутри контейнера (например, миграции вручную):
   ```bash
   docker-compose run --rm web python manage.py migrate
   ```
