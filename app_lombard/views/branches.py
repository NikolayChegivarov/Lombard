from django.shortcuts import render
from ..models import Branch
import json
from django.utils import timezone
from collections import defaultdict


def branches_view(request):
    # Получаем все активные филиалы
    branches = Branch.objects.filter(is_active=True).prefetch_related('working_hours')

    # Группируем филиалы по городам
    cities_dict = defaultdict(list)

    for branch in branches:
        # Получаем расписание для каждого филиала
        schedule = []
        working_hours = branch.working_hours.all().order_by('day_of_week')

        for wh in working_hours:
            if wh.is_closed:
                time_str = "Выходной"
            else:
                open_time = wh.opening_time.strftime('%H:%M') if wh.opening_time else '--:--'
                close_time = wh.closing_time.strftime('%H:%M') if wh.closing_time else '--:--'
                time_str = f"{open_time} - {close_time}"

            schedule.append({
                'day': wh.get_day_of_week_display(),
                'time': time_str,
                'is_closed': wh.is_closed
            })

        # Проверяем, открыт ли филиал сейчас
        is_open_now = branch.is_open_now()

        branch_data = {
            'id': branch.id,
            'city': branch.city,
            'address': f"{branch.street}, {branch.house}",
            'phone': branch.phone,
            'formatted_phone': branch.get_formatted_phone(),  # ← ДОБАВЛЕНО
            'description': branch.description,
            'latitude': float(branch.latitude) if branch.latitude else None,
            'longitude': float(branch.longitude) if branch.longitude else None,
            'schedule': schedule,
            'is_open_now': is_open_now,
            'status_color': 'green' if is_open_now else 'red',
            'status_text': 'Открыт' if is_open_now else 'Закрыт'
        }

        cities_dict[branch.city].append(branch_data)

    # Формируем данные для городов
    cities_data = []
    for city, city_branches in cities_dict.items():
        cities_data.append({
            'city': city,
            'branch_count': len(city_branches),
            'branches': city_branches
        })

    # Сортируем города по алфавиту
    cities_data.sort(key=lambda x: x['city'])

    # Данные для JSON (для карт)
    cities_json_data = []
    for city_data in cities_data:
        cities_json_data.append({
            'city': city_data['city'],
            'branches': [b for b in city_data['branches'] if b['latitude'] and b['longitude']]
        })

    context = {
        'cities': cities_data,
        'cities_json': json.dumps(cities_json_data, ensure_ascii=False),
        'total_branches': len(branches),
        'active_branches': len([b for b in branches if b.is_open_now()])
    }

    return render(request, 'branches.html', context)