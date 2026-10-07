"""
Context processor для передачи информации о выбранном городе
и настроек во все шаблоны проекта.

Доступные переменные в шаблонах:
    - selected_city        : str | None — текущий город пользователя
    - all_cities           : list[str]  — список городов, где есть активные филиалы
    - need_city_confirm    : bool       — нужно ли показать модалку выбора города
    - YANDEX_MAPS_API_KEY  : str        — API-ключ Яндекс.Карт (может быть пустым)
"""

from urllib.parse import unquote

from django.conf import settings

from app_branches.models import Branch


def city_context(request):
    """
    Добавляет в контекст всех шаблонов информацию о выбранном городе
    и публичные настройки (например, API-ключ Яндекс.Карт).
    """

    # Список городов, где есть активные филиалы (отсортирован по алфавиту)
    all_cities = list(
        Branch.objects
        .filter(is_active=True)
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    # Читаем город из cookie с URL-decode
    raw_city = request.COOKIES.get('selected_city', '')
    selected_city = unquote(raw_city) if raw_city else ''

    # Если город не выбран или его больше нет в списке — берём первый доступный
    if not selected_city or selected_city not in all_cities:
        selected_city = all_cities[0] if all_cities else None

    # Нужно ли показать модалку подтверждения города
    need_city_confirm = request.COOKIES.get('city_confirmed') != '1'

    return {
        'selected_city': selected_city,
        'all_cities': all_cities,
        'need_city_confirm': need_city_confirm,
        'YANDEX_MAPS_API_KEY': settings.API_KEY_YANDEX_MAP,
    }