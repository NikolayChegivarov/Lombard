from django.contrib import admin
from django.utils.html import format_html
from .models import Branch, WorkingHours


class WorkingHoursInline(admin.TabularInline):
    """Режим работы в виде inline в филиале"""
    model = WorkingHours
    extra = 7  # Все дни недели
    max_num = 7  # Не больше 7 дней
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        """Предзаполняем дни недели для нового филиала"""
        formset = super().get_formset(request, obj, **kwargs)
        if not obj:  # Если создаем новый филиал
            formset.form.base_fields['day_of_week'].initial = 0
        return formset


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
        if obj.pk:
            hours = obj.working_hours.all().order_by('day_of_week')
            if not hours:
                return "Режим работы не установлен"

            html = '<div style="max-width: 300px;">'
            for hour in hours:
                status = "❌ Выходной" if hour.is_closed else f"✅ {hour.opening_time.strftime('%H:%M')} - {hour.closing_time.strftime('%H:%M')}"
                html += f'<div><strong>{hour.get_day_of_week_display()}:</strong> {status}</div>'
            html += '</div>'
            return format_html(html)
        return "Сначала сохраните филиал, чтобы установить режим работы"

    working_hours_preview.short_description = 'Текущий режим работы'

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).prefetch_related('working_hours')

    def save_formset(self, request, form, formset, change):
        """Автоматически создаем все дни недели при создании филиала"""
        instances = formset.save(commit=False)

        # Если создаем новый филиал, заполняем все дни недели
        if not change and instances:
            branch = form.instance
            existing_days = {instance.day_of_week for instance in instances if instance.day_of_week is not None}

            # Создаем недостающие дни недели
            for day in range(7):
                if day not in existing_days:
                    WorkingHours.objects.create(
                        branch=branch,
                        day_of_week=day,
                        is_closed=(day == 6)  # Воскресенье по умолчанию выходной
                    )

        for instance in instances:
            instance.save()


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    """Отдельная админка для режима работы (если нужна)"""
    list_display = ['branch', 'day_of_week', 'opening_time', 'closing_time', 'is_closed']
    list_filter = ['branch', 'day_of_week', 'is_closed']
    search_fields = ['branch__city', 'branch__street']
    list_editable = ['opening_time', 'closing_time', 'is_closed']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('branch')