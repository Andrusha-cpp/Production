# Production
Репозиторий проекта по Питону "Тотализатор Мисс РФиКТ"

## Локальный запуск
1. Установите зависимости (Python 3.12+):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
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
