from django.shortcuts import render
from django.shortcuts import render
from django.utils import timezone
from app_lombard.models import MetalPrice


def prices_view(request):
    # Получаем цены, разделенные по типам металлов
    gold_prices = MetalPrice.objects.filter(metal_type='gold').order_by('sample')
    silver_prices = MetalPrice.objects.filter(metal_type='silver').order_by('sample')

    # Получаем самую позднюю дату обновления среди всех цен
    latest_update = MetalPrice.objects.all().order_by('-created_at').first()

    context = {
        'gold_prices': gold_prices,
        'silver_prices': silver_prices,
        'latest_update': latest_update.created_at if latest_update else timezone.now(),
    }

    return render(request, 'prices.html', context)

def index(request):
    return render(request, 'index.html')

def questions_answers_view(request):
    return render(request, 'questions_answers.html')

def news_view(request):
    return render(request, 'news.html')

def contacts_view(request):
    return render(request, 'contacts.html')