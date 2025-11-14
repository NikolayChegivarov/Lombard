from django.shortcuts import render
from ..models import Branch
import json
from django.utils import timezone


def branches_view(request):
    # Получаем все активные филиалы
    branches = Branch.objects.filter(is_active=True).prefetch_related('working_hours')

    # Подготавливаем данные для карты
    branches_data = []
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

        branches_data.append({
            'id': branch.id,
            'city': branch.city,
            'address': f"{branch.street}, {branch.house}",
            'phone': branch.phone,
            'description': branch.description,
            'latitude': float(branch.latitude) if branch.latitude else None,
            'longitude': float(branch.longitude) if branch.longitude else None,
            'schedule': schedule,
            'is_open_now': is_open_now,
            'status_color': 'green' if is_open_now else 'red',
            'status_text': 'Открыт' if is_open_now else 'Закрыт'
        })

    # Фильтруем филиалы с координатами для карты
    branches_with_coords = [b for b in branches_data if b['latitude'] and b['longitude']]

    context = {
        'branches': branches_data,
        'branches_json': json.dumps(branches_with_coords, ensure_ascii=False),
        'total_branches': len(branches_data),
        'active_branches': len([b for b in branches_data if b['is_open_now']])
    }

    return render(request, 'branches.html', context)