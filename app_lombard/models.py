from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import RegexValidator


phone_validator = RegexValidator(
    regex=r'^(\+7|8)[0-9]{10}$',
    message='Телефон должен быть в формате +7XXXXXXXXXX или 8XXXXXXXXXX'
)

class WorkingHours(models.Model):
    """Расписание"""
    DAYS_OF_WEEK = [
        (0, 'Понедельник'),
        (1, 'Вторник'),
        (2, 'Среда'),
        (3, 'Четверг'),
        (4, 'Пятница'),
        (5, 'Суббота'),
        (6, 'Воскресенье'),
    ]

    id = models.AutoField(primary_key=True, verbose_name='ID')
    branch = models.ForeignKey(
        'Branch',
        on_delete=models.CASCADE,
        related_name='working_hours',
        verbose_name='Филиал'
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name='День недели')
    opening_time = models.TimeField(verbose_name='Время открытия', null=True, blank=True)
    closing_time = models.TimeField(verbose_name='Время закрытия', null=True, blank=True)
    is_closed = models.BooleanField(default=False, verbose_name='Выходной')

    class Meta:
        verbose_name = 'Режим работы'
        verbose_name_plural = 'Режимы работы'
        ordering = ['branch', 'day_of_week']
        unique_together = ['branch', 'day_of_week']

    def clean(self):
        if not self.is_closed:
            if not self.opening_time or not self.closing_time:
                raise ValidationError('Для рабочих дней необходимо указать время открытия и закрытия')
            if self.opening_time >= self.closing_time:
                raise ValidationError('Время открытия должно быть раньше времени закрытия')

    def __str__(self):
        if self.is_closed:
            return f"{self.get_day_of_week_display()}: выходной"

        return f"{self.get_day_of_week_display()}: {self.opening_time.strftime('%H:%M')} - {self.closing_time.strftime('%H:%M')}"


class Branch(models.Model):
    """Филиалы"""
    id = models.AutoField(primary_key=True, verbose_name='ID')
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house = models.CharField(max_length=10, verbose_name='Дом')
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
        validators=[phone_validator]
    )
    description = models.TextField(verbose_name="Описание", blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    # Координаты - основа для карты
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ['city', 'street']

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}"

    def get_formatted_phone(self):
        """Возвращает отформатированный номер телефона"""
        phone = self.phone.strip()

        # Убираем все нецифровые символы
        digits = ''.join(filter(str.isdigit, phone))

        # Форматируем номер
        if len(digits) == 11:
            if digits.startswith('8'):
                return f'+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}'
            elif digits.startswith('7'):
                return f'+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:]}'
        elif len(digits) == 10:
            return f'+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}'

        # Если не удалось отформатировать, возвращаем как есть
        return phone

    def get_address(self):
        """Возвращает полный адрес"""
        return f"{self.street}, {self.house}"

    def get_working_hours_display(self):
        """Возвращает отформатированное представление режима работы"""
        hours = self.working_hours.all()
        if not hours:
            return "Режим работы не установлен"

        return "\n".join(str(hour) for hour in hours)

    def is_open_now(self):
        """Проверяет, открыт ли филиал в текущий момент"""
        now = timezone.now()
        today = now.weekday()
        current_time = now.time()

        try:
            today_hours = self.working_hours.get(day_of_week=today)
            if today_hours.is_closed:
                return False
            return today_hours.opening_time <= current_time <= today_hours.closing_time
        except WorkingHours.DoesNotExist:
            return False