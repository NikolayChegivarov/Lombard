# views/main_views.py
from urllib.parse import unquote

from django.shortcuts import render
from django.utils import timezone

from app_branches.models import Branch
from app_prices.models import MetalPrice
from app_branches.views import _serialize_branch


def index(request):
    """
    Главная страница. Отдаёт шаблон + филиалы текущего города (из cookie).
    Город берётся из cookie selected_city (URL-decode) или первый доступный.
    """
    # Все города, где есть активные филиалы
    all_cities = list(
        Branch.objects
        .filter(is_active=True)
        .values_list('city', flat=True)
        .distinct()
        .order_by('city')
    )

    # 👇 ВАЖНО: декодируем URL-encoded cookie
    raw_city = request.COOKIES.get('selected_city', '')
    selected_city = unquote(raw_city) if raw_city else ''

    if not selected_city or selected_city not in all_cities:
        selected_city = all_cities[0] if all_cities else None

    # Филиалы выбранного города
    branches = []
    if selected_city:
        branches_qs = (
            Branch.objects
            .filter(is_active=True, city=selected_city)
            .prefetch_related('working_hours')
            .order_by('street', 'house')
        )
        branches = [_serialize_branch(b) for b in branches_qs]

    context = {
        'branches_json': branches,
    }
    return render(request, 'index.html', context)


def prices_view(request):
    gold_prices = MetalPrice.objects.filter(metal_type='gold').order_by('sample')
    silver_prices = MetalPrice.objects.filter(metal_type='silver').order_by('sample')
    latest_update = MetalPrice.objects.all().order_by('-created_at').first()

    context = {
        'gold_prices': gold_prices,
        'silver_prices': silver_prices,
        'latest_update': latest_update.created_at if latest_update else timezone.now(),
    }
    return render(request, 'prices.html', context)


def questions_answers_view(request):
    return render(request, 'questions_answers.html')


def news_view(request):
    return render(request, 'news.html')


def contacts_view(request):
    return render(request, 'base/contacts.html')


def about_us(request):
    active_branches_count = Branch.objects.filter(is_active=True).count()

    context = {
        'active_branches_count': active_branches_count,
        'title': 'О нас | Ломбард Народный',
    }

    return render(request, 'base/about_us.html', context)