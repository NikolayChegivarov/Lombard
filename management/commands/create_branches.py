from django.core.management.base import BaseCommand
from django.utils import timezone
from app_lombard.models import Branch, WorkingHours


class Command(BaseCommand):
    help = 'Создание тестовых филиалов'

    def handle(self, *args, **options):
        # Основной филиал в Костроме
        branch, created = Branch.objects.get_or_create(
            city='Кострома',
            street='Самоковская',
            house='10Б',
            defaults={
                'phone': '+7 (4942) 123-456',
                'description': 'Главный филиал ломбарда',
                'latitude': 57.7680,
                'longitude': 40.9269,
            }
        )

        if created:
            # Создаем режим работы для всех дней недели
            working_hours_data = [
                (0, '09:00', '19:00', False),  # Пн
                (1, '09:00', '19:00', False),  # Вт
                (2, '09:00', '19:00', False),  # Ср
                (3, '09:00', '19:00', False),  # Чт
                (4, '09:00', '19:00', False),  # Пт
                (5, '10:00', '17:00', False),  # Сб
                (6, None, None, True),         # Вс - выходной
            ]

            for day, open_time, close_time, closed in working_hours_data:
                WorkingHours.objects.create(
                    branch=branch,
                    day_of_week=day,
                    opening_time=open_time,
                    closing_time=close_time,
                    is_closed=closed
                )

            self.stdout.write(
                self.style.SUCCESS(f'Создан филиал: {branch}')
            )
        else:
            self.stdout.write('Филиал уже существует')