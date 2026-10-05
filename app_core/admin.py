from django.contrib import admin
from django.utils.html import format_html
from django.forms import BaseInlineFormSet
from django import forms
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from decimal import Decimal, InvalidOperation

from app_branches.models import Branch, WorkingHours
from app_prices.models import MetalPrice

from .views.price_calculator import price_calculator
from django.contrib import messages

# --------------------------РАСПИСАНИЕ--------------------------------------------------------------------------------
class WorkingHoursForm(forms.ModelForm):
    """Кастомная форма для времени с предустановленными значениями"""

    opening_time = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('07:00:00', '07:00'),
            ('08:00:00', '08:00'),
            ('09:00:00', '09:00'),
            ('10:00:00', '10:00'),
            ('11:00:00', '11:00'),
        ],
        required=False,
        label='Время открытия'
    )

    closing_time = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('18:00:00', '18:00'),
            ('19:00:00', '19:00'),
            ('20:00:00', '20:00'),
            ('21:00:00', '21:00'),
            ('22:00:00', '22:00'),
        ],
        required=False,
        label='Время закрытия'
    )

    class Meta:
        model = WorkingHours
        fields = '__all__'


class WorkingHoursFormSet(BaseInlineFormSet):
    """Кастомный FormSet для автоматического создания дней недели"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        instance = kwargs.get('instance')

        # Если это новый филиал (нет primary key)
        if instance is None or instance.pk is None:
            # Создаем начальные данные для всех дней недели
            self.initial = [
                {'day_of_week': day, 'is_closed': False}
                # 👈 Убрал (day == 6) - теперь все дни по умолчанию НЕ выходные
                for day in range(7)
            ]
            self.extra = 7


class WorkingHoursInline(admin.TabularInline):
    """Режим работы в виде inline в филиале"""
    model = WorkingHours
    form = WorkingHoursForm
    formset = WorkingHoursFormSet
    extra = 7  # Показываем все 7 дней недели
    max_num = 7  # Не больше 7 дней
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        """Автоматически создаем все дни недели для нового филиала"""
        if obj is None or obj.pk is None:
            kwargs['formset'] = WorkingHoursFormSet
        return super().get_formset(request, obj, **kwargs)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    """Админка для филиалов"""
    list_display = [
        'city',
        'street',
        'house',
        'phone',
        'is_active',
        'is_open_now_display',
        'created_at'
    ]
    list_filter = ['is_active', 'city', 'created_at']
    search_fields = ['city', 'street', 'house', 'phone']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at', 'working_hours_preview']
    inlines = [WorkingHoursInline]
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'city',
                'street',
                'house',
                'phone',
                'is_active'
            )
        }),
        ('Описание', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Координаты для карты', {
            'fields': ('latitude', 'longitude'),
            'description': 'Используются для отображения на карте'
        }),
        ('Режим работы', {
            'fields': ('working_hours_preview',),
            'classes': ('collapse', 'wide')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_related(self, request, form, formsets, change):
        """Сохраняем связанные объекты (расписание)"""
        # Сначала сохраняем филиал
        super().save_related(request, form, formsets, change)

        # Для нового филиала проверяем, создалось ли расписание
        if not change:  # Если это создание нового филиала
            branch = form.instance

            # Удаляем возможные дубликаты, созданные формой
            branch.working_hours.all().delete()

            # Создаем правильное расписание на основе данных из формы
            for formset in formsets:
                if formset.model == WorkingHours:
                    instances = formset.save(commit=False)
                    for instance in instances:
                        # Проверяем, что это валидная запись (не пустая форма)
                        if instance.day_of_week is not None:
                            instance.branch = branch
                            instance.save()

    def is_open_now_display(self, obj):
        """Отображение статуса открыт/закрыт в списке"""
        if obj.is_open_now():
            return format_html(
                '<span style="color: green; font-weight: bold;">● Открыт</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">● Закрыт</span>'
            )

    is_open_now_display.short_description = 'Статус'
    is_open_now_display.admin_order_field = 'is_active'

    def working_hours_preview(self, obj):
        """Предпросмотр режима работы"""
        if obj.pk:  # Проверяем, что филиал сохранен в БД
            hours = obj.working_hours.all().order_by('day_of_week')
            if not hours:
                return "Режим работы не установлен"

            html = '<div style="max-width: 300px;">'
            for hour in hours:
                if hour.is_closed:
                    status = "❌ Выходной"
                else:
                    open_time = hour.opening_time.strftime('%H:%M') if hour.opening_time else '--:--'
                    close_time = hour.closing_time.strftime('%H:%M') if hour.closing_time else '--:--'
                    status = f"✅ {open_time} - {close_time}"
                html += f'<div><strong>{hour.get_day_of_week_display()}:</strong> {status}</div>'
            html += '</div>'
            return format_html(html)
        return "Сначала сохраните филиал, чтобы установить режим работы"

    working_hours_preview.short_description = 'Текущий режим работы'

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).prefetch_related('working_hours')


# --------------------------ФИЛИАЛЫ-----------------------------------------------------------------------------------
@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    """Отдельная админка для режима работы"""
    form = WorkingHoursForm
    list_display = ['branch', 'day_of_week_display', 'opening_time', 'closing_time', 'is_closed']
    list_filter = ['branch', 'day_of_week', 'is_closed']
    search_fields = ['branch__city', 'branch__street']
    list_editable = ['opening_time', 'closing_time', 'is_closed']
    ordering = ['branch', 'day_of_week']

    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()

    day_of_week_display.short_description = 'День недели'
    day_of_week_display.admin_order_field = 'day_of_week'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('branch')


# --------------------------Цены на пробы------------------------------------------------------------------------------
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
        """Запрещаем добавление через стандартную форму"""
        return False

    def has_change_permission(self, request, obj=None):
        """Запрещаем редактирование отдельных записей"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Теперь разрешаем удаление всех записей, т.к. нет статуса active/inactive"""
        return True  # Разрешаем удаление, т.к. нет поля is_active

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
        """Кастомное отображение списка цен"""
        extra_context = extra_context or {}

        # Получаем текущие активные цены
        current_prices = MetalPrice.get_current_prices_dict()

        # Подготавливаем данные для отображения
        prices_display = []

        # Золото
        for sample in [375, 500, 585, 750, 850]:
            key = f"gold_{sample}"
            prices_display.append({
                'metal': 'gold',
                'sample': sample,
                'current_price': current_prices.get(key, '—'),
            })

        # Серебро
        prices_display.append({
            'metal': 'silver',
            'sample': 925,
            'current_price': current_prices.get('silver_925', '—'),
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
        """Представление для обновления цен"""
        context = {
            **self.admin_site.each_context(request),
            'title': 'Обновление цен на пробы',
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        }

        # Получаем текущие цены
        current_prices = MetalPrice.get_current_prices_dict()

        if request.method == 'POST':
            if 'calculate' in request.POST or 'recalculate' in request.POST:
                # Расчет новых цен
                try:
                    gold_585_price_str = request.POST.get('gold_585_price', '0').replace(',', '.')
                    silver_925_price_str = request.POST.get('silver_925_price', '0').replace(',', '.')

                    gold_585_price = Decimal(gold_585_price_str) if gold_585_price_str else Decimal('0')
                    silver_925_price = Decimal(silver_925_price_str) if silver_925_price_str else Decimal('0')

                    if gold_585_price <= 0 or silver_925_price <= 0:
                        raise ValueError("Цена должна быть больше 0")

                    # Рассчитываем цены для золота
                    calculated_gold = price_calculator(gold_585_price)

                    # Получаем введенные пользователем цены (или рассчитанные по умолчанию)
                    calculated_prices = {}
                    gold_samples = [375, 500, 585, 750, 850]

                    for sample in gold_samples:
                        field_name = f'gold_{sample}_price'
                        user_price_str = request.POST.get(field_name, '').replace(',', '.')

                        if user_price_str:
                            calculated_prices[f'gold_{sample}'] = Decimal(user_price_str)
                        else:
                            # Используем рассчитанную цену
                            proba_key = f'proba_{sample}'
                            calculated_prices[f'gold_{sample}'] = calculated_gold.get(proba_key, Decimal('0'))

                    # Для серебра
                    calculated_prices['silver_925'] = silver_925_price

                    context.update({
                        'calculated_prices': calculated_prices,
                        'gold_585_price': gold_585_price,
                        'silver_925_price': silver_925_price,
                        'show_results': True,
                    })

                except (ValueError, TypeError, InvalidOperation) as e:
                    messages.error(request, f'Ошибка ввода: {str(e)}')

            elif 'save' in request.POST:
                # Сохранение новых цен
                try:
                    gold_585_price_str = request.POST.get('gold_585_price', '0').replace(',', '.')
                    silver_925_price_str = request.POST.get('silver_925_price', '0').replace(',', '.')

                    gold_585_price = Decimal(gold_585_price_str) if gold_585_price_str else Decimal('0')
                    silver_925_price = Decimal(silver_925_price_str) if silver_925_price_str else Decimal('0')

                    # Проверка базовых цен
                    if gold_585_price <= 0 or silver_925_price <= 0:
                        raise ValueError("Цена должна быть больше 0")

                    # Собираем все цены из формы
                    gold_prices = {}
                    gold_samples = [375, 500, 585, 750, 850]

                    for sample in gold_samples:
                        field_name = f'gold_{sample}_price'
                        price_str = request.POST.get(field_name, '').replace(',', '.')

                        if not price_str:
                            # Если цена не указана, используем рассчитанную по умолчанию
                            calculated_gold = price_calculator(gold_585_price)
                            proba_key = f'proba_{sample}'
                            price = calculated_gold.get(proba_key, Decimal('0'))
                        else:
                            try:
                                price = Decimal(price_str)
                            except InvalidOperation:
                                raise ValueError(f"Некорректная цена для пробы {sample}")

                        gold_prices[sample] = price

                    # Обновляем цены в базе
                    self.update_all_prices_in_db(gold_585_price, silver_925_price, gold_prices)

                    messages.success(request, 'Цены успешно обновлены!')
                    return HttpResponseRedirect('../')

                except Exception as e:
                    messages.error(request, f'Ошибка при сохранении: {str(e)}')

        context.update({
            'current_prices': current_prices,
            'show_results': 'show_results' in context and context['show_results'],
        })

        return render(request, 'admin/metal_price_update.html', context)

    def update_all_prices_in_db(self, gold_585_price, silver_925_price, gold_prices):
        """Обновить все цены в базе данных"""
        # Для золота
        gold_samples = [375, 500, 585, 750, 850]
        for sample in gold_samples:
            price = gold_prices.get(sample, Decimal('0'))

            # Обновляем или создаем
            MetalPrice.objects.update_or_create(
                metal_type='gold',
                sample=sample,
                defaults={'price_per_gram': price}
            )

        # Для серебра
        MetalPrice.objects.update_or_create(
            metal_type='silver',
            sample=925,
            defaults={'price_per_gram': silver_925_price}
        )