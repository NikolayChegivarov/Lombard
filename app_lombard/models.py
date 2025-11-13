from django.db import models


class Branch(models.Model):
    city = models.CharField(max_length=100, verbose_name='Город')
    street = models.CharField(max_length=200, verbose_name='Улица')
    house = models.CharField(max_length=10, verbose_name='Дом')
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    # Координаты - основа для карты
    latitude = models.FloatField(verbose_name='Широта')
    longitude = models.FloatField(verbose_name='Долгота')

    def __str__(self):
        return f"{self.city}, {self.street}, {self.house}"

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'