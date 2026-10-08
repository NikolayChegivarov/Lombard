"""
Пользовательские калькуляторы для публичной части сайта.
Округление — до целых рублей.
"""
from decimal import Decimal, ROUND_HALF_UP
from django.http import JsonResponse

from ..models import MetalPrice


# Пробы, которые показываем на сайте (в порядке отображения)
GOLD_SAMPLES = [375, 500, 585, 750, 850]
SILVER_SAMPLES = [875, 925]


def _round_rub(value):
    """Округление до целого рубля (математическое, не банковское)."""
    if value is None:
        return 0
    return int(Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def get_metal_prices_for_site():
    """
    Возвращает цены для публичного блока в виде:
    {
        "gold":   {375: 1234, 500: ..., 585: ..., 750: ..., 850: ...},
        "silver": {875: ..., 925: ...},
    }
    Цены — целые рубли. Пробы, для которых нет цены в БД, отсутствуют в словаре.
    """
    prices_db = MetalPrice.get_current_prices_dict()

    result = {"gold": {}, "silver": {}}

    for sample in GOLD_SAMPLES:
        key = f"gold_{sample}"
        if key in prices_db:
            result["gold"][sample] = _round_rub(prices_db[key])

    for sample in SILVER_SAMPLES:
        key = f"silver_{sample}"
        if key in prices_db:
            result["silver"][sample] = _round_rub(prices_db[key])

    return result


def metal_prices_api(request):
    """JSON-эндпоинт: актуальные цены для публичного калькулятора."""
    return JsonResponse(get_metal_prices_for_site())