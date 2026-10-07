"""
Views для приложения app_branches.

Содержит AJAX-endpoint'ы:
    - set_city_view     : сохранение выбранного города в cookie
    - branches_api_view : JSON со списком филиалов текущего города
"""

from urllib.parse import quote, unquote

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from app_branches.models import Branch


# ==============================================================================
# ХЕЛПЕР: сериализация филиала в JSON
# ==============================================================================

def _serialize_branch(branch):
    """
    Преобразует объект Branch в словарь для JSON-ответа.
    Включает расписание и текущий статус (открыт/закрыт).
    """
    schedule = []
    working_hours = branch.working_hours.all().order_by('day_of_week')

    for wh in working_hours:
        if wh.is_closed:
            time_str = "Выходной"
        else:
            open_time = wh.opening_time.strftime('%H:%M') if wh.opening_time else '--:--'
            close_time = wh.closing_time.strftime('%H:%M') if wh.closing_time else '--:--'
            time_str = f"{open_time}–{close_time}"

        schedule.append({
            'day': wh.get_day_of_week_display(),
            'time': time_str,
            'is_closed': wh.is_closed,
        })

    is_open = branch.is_open_now()
    photo_url = branch.photo.url if branch.photo else None

    return {
        'id': branch.id,
        'city': branch.city,
        'street': branch.street,
        'house': branch.house,
        'address': f"{branch.street}, {branch.house}",
        'phone': branch.phone,
        'formatted_phone': branch.get_formatted_phone(),
        'description': branch.description,
        'latitude': float(branch.latitude) if branch.latitude else None,
        'longitude': float(branch.longitude) if branch.longitude else None,
        'photo': photo_url,
        'schedule': schedule,
        'is_open_now': is_open,
        'status_text': 'Открыт' if is_open else 'Закрыт',
    }


# ==============================================================================
# ХЕЛПЕР: чтение города из cookie (с URL-decode)
# ==============================================================================

def _get_city_from_cookie(request):
    """
    Читает город из cookie selected_city и URL-декодирует.
    Возвращает пустую строку, если cookie нет.
    """
    raw = request.COOKIES.get('selected_city', '')
    if not raw:
        return ''
    try:
        return unquote(raw)
    except Exception:
        return raw


# ==============================================================================
# AJAX: сохранение выбранного города
# ==============================================================================

@require_POST
def set_city_view(request):
    """
    POST /api/set-city/
    Body: city=<название города>
    Ставит cookie selected_city (URL-encoded) и city_confirmed=1.
    Возвращает JSON {ok: true, city: <город>}.
    """
    city = request.POST.get('city', '').strip()

    if not city:
        return JsonResponse(
            {'ok': False, 'error': 'Не указан город'},
            status=400,
        )

    exists = Branch.objects.filter(is_active=True, city=city).exists()

    if not exists:
        return JsonResponse(
            {'ok': False, 'error': f'Город «{city}» не найден'},
            status=404,
        )

    # Кодируем кириллицу в ASCII-безопасную форму
    encoded_city = quote(city)

    response = JsonResponse({'ok': True, 'city': city})
    response.set_cookie(
        'selected_city',
        encoded_city,
        max_age=60 * 60 * 24 * 365,  # 1 год
        samesite='Lax',
    )
    response.set_cookie(
        'city_confirmed',
        '1',
        max_age=60 * 60 * 24 * 365,
        samesite='Lax',
    )
    return response


# ==============================================================================
# AJAX: список филиалов текущего города
# ==============================================================================

@require_GET
def branches_api_view(request):
    """
    GET /api/branches/?city=<город>  (city — опционально)
    Если city не передан — берётся из cookie selected_city (URL-decode).
    Если и там нет — берётся первый город из БД.
    """
    city = request.GET.get('city', '').strip()

    if not city:
        city = _get_city_from_cookie(request)

    if not city:
        city = (
            Branch.objects
            .filter(is_active=True)
            .values_list('city', flat=True)
            .order_by('city')
            .first()
        )

    branches_qs = (
        Branch.objects
        .filter(is_active=True, city=city)
        .prefetch_related('working_hours')
        .order_by('street', 'house')
    )

    branches_data = [_serialize_branch(b) for b in branches_qs]

    return JsonResponse(
        {
            'city': city,
            'branches': branches_data,
        },
        json_dumps_params={'ensure_ascii': False, 'indent': 2},
    )