from django.db import models
from django.core.validators import MinValueValidator


class MetalPrice(models.Model):
    """Цены на пробы металлов"""
    METAL_CHOICES = [
        ('gold', 'Золото'),
        ('silver', 'Серебро'),
    ]

    id = models.AutoField(primary_key=True, verbose_name='ID')
    metal_type = models.CharField(
        max_length=10,
        choices=METAL_CHOICES,
        verbose_name='Тип металла'
    )
    sample = models.IntegerField(
        verbose_name='Проба',
        help_text='375, 500, 585, 750, 850, 925'
    )
    price_per_gram = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Цена за грамм (руб.)',
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Цена металла'
        verbose_name_plural = 'Цены металлов'
        ordering = ['metal_type', 'sample']
        # УБРАТЬ ЭТУ СТРОКУ полностью:
        # unique_together = ['metal_type', 'sample']

    def __str__(self):
        return f"{self.get_metal_type_display()} {self.sample} - {self.price_per_gram} руб./г"

    @classmethod
    def get_current_prices_dict(cls):
        """Получить текущие цены в виде словаря"""
        prices = {}
        for price in cls.objects.all():
            key = f"{price.metal_type}_{price.sample}"
            prices[key] = price.price_per_gram
        return prices