from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from core.models import Candidate


class Command(BaseCommand):
    help = "Seed the database with demo candidates"

    def handle(self, *args, **options):
        media_dir = Path(__file__).parent / "media_seed"
        data = [
            {
                "first_name": "Анна",
                "last_name": "Иванова",
                "patronymic": "Сергеевна",
                "course": 2,
                "group": "КН-21",
                "info": "Студентка 2 курса, активистка",
                "photo": "1.jpeg",
            },
            {
                "first_name": "Мария",
                "last_name": "Петрова",
                "patronymic": "Андреевна",
                "course": 3,
                "group": "ПМИ-31",
                "info": "Участница олимпиад, волонтёр",
                "photo": "2.jpeg",
            },
            {
                "first_name": "Екатерина",
                "last_name": "Смирнова",
                "patronymic": "Игоревна",
                "course": 4,
                "group": "ИС-41",
                "info": "Спортсменка, лидер команды",
                "photo": "3.jpeg",
            },
        ]

        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        (media_root / "candidates").mkdir(parents=True, exist_ok=True)

        created = 0
        for item in data:
            candidate, was_created = Candidate.objects.get_or_create(
                first_name=item["first_name"],
                last_name=item["last_name"],
                patronymic=item["patronymic"],
                defaults={
                    "course": item["course"],
                    "group": item["group"],
                    "info": item["info"],
                },
            )
            photo_path = media_dir / item["photo"]
            if not candidate.photo and photo_path.exists():
                with photo_path.open("rb") as photo_file:
                    candidate.photo.save(
                        f"candidates/{photo_path.name}", File(photo_file), save=True
                    )
            created += 1 if was_created else 0

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} candidates"))
