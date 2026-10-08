from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from decimal import Decimal, InvalidOperation
from django.contrib import messages

from .models import MetalPrice


# ==============================================================================
# ФУНКЦИИ РАСЧЁТА ЦЕН ДЛЯ АДМИНКИ
# ==============================================================================

def price_admin_calculator(main_proba, decimals=0):
    """Расчёт цен на пробы золота от базовой 585 пробы (для админки)."""
    proba_375 = round(main_proba * 375 / 585, decimals)
    proba_500 = round(main_proba * 500 / 585, decimals)
    proba_585 = main_proba
    proba_750 = round(main_proba * 750 / 585, decimals)
    proba_850 = round(main_proba * 850 / 585, decimals)

    return {
        "proba_375": proba_375,
        "proba_500": proba_500,
        "proba_585": proba_585,
        "proba_750": proba_750,
        "proba_850": proba_850,
    }


def silver_price_admin_calculator(base_925_price, decimals=0):
    """Расчёт цен на пробы серебра от базовой 925 пробы (для админки)."""
    proba_875 = round(base_925_price * 875 / 925, decimals)
    proba_925 = base_925_price

    return {
        "proba_875": proba_875,
        "proba_925": proba_925,
    }


# ==============================================================================
# АДМИНКА
# ==============================================================================

@admin.register(MetalPrice)
class MetalPriceAdmin(admin.ModelAdmin):
    """Админка для управления ценами на пробы"""
    change_list_template = 'admin/metal_price_change_list.html'

    list_display = [
        'metal_type_display',
        'sample',
        'price_display',
        'created_at',
    ]
    list_filter = ['metal_type']
    search_fields = ['sample']
    readonly_fields = ['created_at']
    list_per_page = 20

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def metal_type_display(self, obj):
        color = '#FFD700' if obj.metal_type == 'gold' else '#C0C0C0'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_metal_type_display()
        )

    metal_type_display.short_description = 'Металл'

    def price_display(self, obj):
        return f"{obj.price_per_gram} руб./г"

    price_display.short_description = 'Цена'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        current_prices = MetalPrice.get_current_prices_dict()

        prices_display = []

        for sample in [375, 500, 585, 750, 850]:
            key = f"gold_{sample}"
            prices_display.append({
                'metal': 'gold',
                'sample': sample,
                'current_price': current_prices.get(key, '—'),
            })

        for sample in [875, 925]:
            key = f"silver_{sample}"
            prices_display.append({
                'metal': 'silver',
                'sample': sample,
                'current_price': current_prices.get(key, '—'),
            })

        extra_context.update({
            'prices_display': prices_display,
            'title': 'Актуальные цены на металл',
        })

        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'update-prices/',
                self.admin_site.admin_view(self.update_prices_view),
                name='metal_prices_update'
            ),
        ]
        return custom_urls + urls

    def update_prices_view(self, request):
        current_prices = MetalPrice.get_current_prices_dict()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Обновление цен на пробы',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
            'current_prices': current_prices,
            # Предзаполнение полей текущими ценами (строка с точкой — для type="number")
            'gold_585_price': str(current_prices.get('gold_585', '')),
            'silver_925_price': str(current_prices.get('silver_925', '')),
        }

        if request.method == 'POST':
            if 'calculate' in request.POST or 'recalculate' in request.POST:
                try:
                    gold_585_price_str = request.POST.get('gold_585_price', '0').replace(',', '.')
                    silver_925_price_str = request.POST.get('silver_925_price', '0').replace(',', '.')

                    gold_585_price = Decimal(gold_585_price_str) if gold_585_price_str else Decimal('0')
                    silver_925_price = Decimal(silver_925_price_str) if silver_925_price_str else Decimal('0')

                    if gold_585_price <= 0 or silver_925_price <= 0:
                        raise ValueError("Цена должна быть больше 0")

                    # --- Золото ---
                    calculated_gold = price_admin_calculator(gold_585_price)

                    calculated_prices = {}
                    gold_samples = [375, 500, 585, 750, 850]

                    for sample in gold_samples:
                        field_name = f'gold_{sample}_price'
                        user_price_str = request.POST.get(field_name, '').replace(',', '.')

                        if user_price_str:
                            calculated_prices[f'gold_{sample}'] = Decimal(user_price_str)
                        else:
                            proba_key = f'proba_{sample}'
                            calculated_prices[f'gold_{sample}'] = calculated_gold.get(proba_key, Decimal('0'))

                    # --- Серебро ---
                    calculated_silver = silver_price_admin_calculator(silver_925_price)
                    calculated_prices['silver_875'] = calculated_silver['proba_875']
                    calculated_prices['silver_925'] = calculated_silver['proba_925']

                    context.update({
                        'calculated_prices': calculated_prices,
                        'gold_585_price': str(gold_585_price),
                        'silver_925_price': str(silver_925_price),
                        'show_results': True,
                    })

                except (ValueError, TypeError, InvalidOperation) as e:
                    messages.error(request, f'Ошибка ввода: {str(e)}')

            elif 'save' in request.POST:
                try:
                    gold_585_price_str = request.POST.get('gold_585_price', '0').replace(',', '.')
                    silver_925_price_str = request.POST.get('silver_925_price', '0').replace(',', '.')

                    gold_585_price = Decimal(gold_585_price_str) if gold_585_price_str else Decimal('0')
                    silver_925_price = Decimal(silver_925_price_str) if silver_925_price_str else Decimal('0')

                    if gold_585_price <= 0 or silver_925_price <= 0:
                        raise ValueError("Цена должна быть больше 0")

                    # --- Золото ---
                    gold_prices = {}
                    gold_samples = [375, 500, 585, 750, 850]

                    for sample in gold_samples:
                        field_name = f'gold_{sample}_price'
                        price_str = request.POST.get(field_name, '').replace(',', '.')

                        if not price_str:
                            calculated_gold = price_admin_calculator(gold_585_price)
                            proba_key = f'proba_{sample}'
                            price = calculated_gold.get(proba_key, Decimal('0'))
                        else:
                            try:
                                price = Decimal(price_str)
                            except InvalidOperation:
                                raise ValueError(f"Некорректная цена для пробы {sample}")

                        gold_prices[sample] = price

                    # --- Серебро ---
                    silver_prices = silver_price_admin_calculator(silver_925_price)

                    self.update_all_prices_in_db(
                        gold_585_price,
                        silver_925_price,
                        gold_prices,
                        silver_prices,
                    )

                    messages.success(request, 'Цены успешно обновлены!')
                    return HttpResponseRedirect('../')

                except Exception as e:
                    messages.error(request, f'Ошибка при сохранении: {str(e)}')

        context.update({
            'show_results': context.get('show_results', False),
        })

        return render(request, 'admin/metal_price_update.html', context)

    def update_all_prices_in_db(self, gold_585_price, silver_925_price, gold_prices, silver_prices):
        # --- Золото ---
        gold_samples = [375, 500, 585, 750, 850]
        for sample in gold_samples:
            price = gold_prices.get(sample, Decimal('0'))
            MetalPrice.objects.update_or_create(
                metal_type='gold',
                sample=sample,
                defaults={'price_per_gram': price}
            )

        # --- Серебро ---
        MetalPrice.objects.update_or_create(
            metal_type='silver',
            sample=925,
            defaults={'price_per_gram': silver_925_price}
        )

        silver_875 = silver_prices.get('proba_875', Decimal('0'))
        MetalPrice.objects.update_or_create(
            metal_type='silver',
            sample=875,
            defaults={'price_per_gram': silver_875}
        )