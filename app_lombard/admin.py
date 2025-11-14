from django.contrib import admin
from django.utils.html import format_html
from django.forms import BaseInlineFormSet
from django import forms
from .models import Branch, WorkingHours

#--------------------------РАСПИСАНИЕ----------------------------
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

#--------------------------ФИЛИАЛЫ----------------------------
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
