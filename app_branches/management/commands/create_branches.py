"""
Команда для создания тестовых филиалов ломбарда.

Запуск:
    python manage.py create_branches

Опционально:
    python manage.py create_branches --reset
        Удалить все существующие филиалы и создать заново.
"""

from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from app_branches.models import Branch, WorkingHours


# ==============================================================================
# ДАННЫЕ О ФИЛИАЛАХ
# ==============================================================================
# Структура: (город, улица, дом, телефон, широта, долгота, описание)
# ==============================================================================

BRANCHES_DATA = [
    # ---------------------------- КОСТРОМА (5) ----------------------------
    {
        'city': 'Кострома',
        'street': 'Самоковская',
        'house': '10Б',
        'phone': '+7 (4942) 123-456',
        'latitude': 57.7680,
        'longitude': 40.9269,
        'description': 'Главный филиал ломбарда в Костроме',
        'schedule': 'default',  # 09:00-19:00
    },
    {
        'city': 'Кострома',
        'street': 'проспект Мира',
        'house': '45',
        'phone': '+7 (4942) 234-567',
        'latitude': 57.7775,
        'longitude': 40.9438,
        'description': 'Филиал в центре города',
        'schedule': 'default',
    },
    {
        'city': 'Кострома',
        'street': 'Советская',
        'house': '21',
        'phone': '+7 (4942) 345-678',
        'latitude': 57.7685,
        'longitude': 40.9272,
        'description': 'Филиал рядом с центральной площадью',
        'schedule': 'default',
    },
    {
        'city': 'Кострома',
        'street': 'Никитская',
        'house': '68',
        'phone': '+7 (4942) 456-789',
        'latitude': 57.7605,
        'longitude': 40.9380,
        'description': 'Филиал в районе Никитской слободы',
        'schedule': 'default',
    },
    {
        'city': 'Кострома',
        'street': 'Калиновская',
        'house': '42',
        'phone': '+7 (4942) 567-890',
        'latitude': 57.7890,
        'longitude': 40.9720,
        'description': 'Филиал в Заволжском районе',
        'schedule': 'default',
    },

    # ---------------------------- МОСКВА (10) ----------------------------
    {
        'city': 'Москва',
        'street': 'Тверская',
        'house': '12',
        'phone': '+7 (495) 100-10-01',
        'latitude': 55.7610,
        'longitude': 37.6090,
        'description': 'Филиал в центре Москвы',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Ленинградский проспект',
        'house': '63',
        'phone': '+7 (495) 100-10-02',
        'latitude': 55.7920,
        'longitude': 37.5570,
        'description': 'Филиал рядом с метро Аэропорт',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Арбат',
        'house': '24',
        'phone': '+7 (495) 100-10-03',
        'latitude': 55.7500,
        'longitude': 37.5940,
        'description': 'Филиал на Старом Арбате',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Кутузовский проспект',
        'house': '36',
        'phone': '+7 (495) 100-10-04',
        'latitude': 55.7400,
        'longitude': 37.5100,
        'description': 'Филиал в районе Кутузовского',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Ленинский проспект',
        'house': '78',
        'phone': '+7 (495) 100-10-05',
        'latitude': 55.6820,
        'longitude': 37.5530,
        'description': 'Филиал на Ленинском проспекте',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Земляной Вал',
        'house': '27',
        'phone': '+7 (495) 100-10-06',
        'latitude': 55.7540,
        'longitude': 37.6570,
        'description': 'Филиал в районе Чистых прудов',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'проспект Мира',
        'house': '118',
        'phone': '+7 (495) 100-10-07',
        'latitude': 55.8100,
        'longitude': 37.6360,
        'description': 'Филиал рядом с ВДНХ',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Профсоюзная',
        'house': '56',
        'phone': '+7 (495) 100-10-08',
        'latitude': 55.6690,
        'longitude': 37.5620,
        'description': 'Филиал на Профсоюзной',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Автозаводская',
        'house': '18',
        'phone': '+7 (495) 100-10-09',
        'latitude': 55.7070,
        'longitude': 37.6570,
        'description': 'Филиал в районе Автозаводской',
        'schedule': 'moscow',
    },
    {
        'city': 'Москва',
        'street': 'Красная Пресня',
        'house': '24',
        'phone': '+7 (495) 100-10-10',
        'latitude': 55.7600,
        'longitude': 37.5560,
        'description': 'Филиал на Красной Пресне',
        'schedule': 'moscow',
    },

    # ------------------------ САНКТ-ПЕТЕРБУРГ (3) ------------------------
    {
        'city': 'Санкт-Петербург',
        'street': 'Б. Московская',
        'house': '1-3, лит. А',
        'phone': '+7 (812) 200-20-01',
        'latitude': 59.9270,
        'longitude': 30.3350,
        'description': 'Филиал в центре Санкт-Петербурга',
        'schedule': 'spb',
    },
    {
        'city': 'Санкт-Петербург',
        'street': 'Новаторов бульвар',
        'house': '112',
        'phone': '+7 (812) 200-20-02',
        'latitude': 59.8590,
        'longitude': 30.2720,
        'description': 'Филиал в Кировском районе',
        'schedule': 'spb',
    },
    {
        'city': 'Санкт-Петербург',
        'street': 'Энгельса проспект',
        'house': '111, пом. 48Н',
        'phone': '+7 (812) 200-20-03',
        'latitude': 60.0330,
        'longitude': 30.3070,
        'description': 'Филиал в Выборгском районе',
        'schedule': 'spb',
    },
]


# ==============================================================================
# ШАБЛОНЫ РАСПИСАНИЯ
# ==============================================================================
# Формат: список кортежей (day_of_week, opening_time, closing_time, is_closed)
# 0 = Пн, 1 = Вт, ..., 6 = Вс
# ==============================================================================

SCHEDULES = {
    # Стандартный график (Кострома)
    'default': [
        (0, time(9, 0),  time(19, 0), False),  # Пн
        (1, time(9, 0),  time(19, 0), False),  # Вт
        (2, time(9, 0),  time(19, 0), False),  # Ср
        (3, time(9, 0),  time(19, 0), False),  # Чт
        (4, time(9, 0),  time(19, 0), False),  # Пт
        (5, time(10, 0), time(17, 0), False),  # Сб
        (6, None,        None,        True),   # Вс — выходной
    ],
    # Москва: 10:00–20:00 по будням
    'moscow': [
        (0, time(10, 0), time(20, 0), False),
        (1, time(10, 0), time(20, 0), False),
        (2, time(10, 0), time(20, 0), False),
        (3, time(10, 0), time(20, 0), False),
        (4, time(10, 0), time(20, 0), False),
        (5, time(10, 0), time(18, 0), False),
        (6, time(10, 0), time(18, 0), False),
    ],
    # СПб: ежедневно 10:00–20:00
    'spb': [
        (0, time(10, 0), time(20, 0), False),
        (1, time(10, 0), time(20, 0), False),
        (2, time(10, 0), time(20, 0), False),
        (3, time(10, 0), time(20, 0), False),
        (4, time(10, 0), time(20, 0), False),
        (5, time(10, 0), time(20, 0), False),
        (6, time(10, 0), time(20, 0), False),
    ],
}


# ==============================================================================
# КОМАНДА
# ==============================================================================

class Command(BaseCommand):
    help = 'Создание тестовых филиалов (Кострома, Москва, Санкт-Петербург)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Удалить все существующие филиалы и создать заново',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠  Удаляем все существующие филиалы...'))
            deleted_count, _ = Branch.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'   Удалено объектов: {deleted_count}'))
            self.stdout.write('')

        created_count = 0
        skipped_count = 0

        for data in BRANCHES_DATA:
            branch, created = Branch.objects.get_or_create(
                city=data['city'],
                street=data['street'],
                house=data['house'],
                defaults={
                    'phone': data['phone'],
                    'description': data['description'],
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'is_active': True,
                }
            )

            if created:
                # Создаём расписание
                schedule_key = data.get('schedule', 'default')
                schedule_data = SCHEDULES.get(schedule_key, SCHEDULES['default'])

                for day, open_time, close_time, is_closed in schedule_data:
                    WorkingHours.objects.create(
                        branch=branch,
                        day_of_week=day,
                        opening_time=open_time,
                        closing_time=close_time,
                        is_closed=is_closed,
                    )

                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Создан: {branch}')
                )
            else:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  – Уже существует: {branch}')
                )

        # Итоги
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'  Создано филиалов:    {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Пропущено (уже были): {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Всего в БД:          {Branch.objects.count()}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Разбивка по городам
        self.stdout.write('')
        self.stdout.write('  По городам:')
        for city in Branch.objects.values_list('city', flat=True).distinct().order_by('city'):
            count = Branch.objects.filter(city=city).count()
            self.stdout.write(f'    • {city}: {count} филиал(ов)')
        self.stdout.write('')