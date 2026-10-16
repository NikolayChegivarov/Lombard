from django.db import models


def carousel_image_upload_to(instance, filename):
    return f'carousel/{filename}'


class CarouselImage(models.Model):
    """Изображение для карусели на главной странице."""

    image = models.ImageField(
        'Изображение',
        upload_to=carousel_image_upload_to,
        help_text='Рекомендуемый размер: 1600×600 px и больше',
    )
    title = models.CharField(
        'Подпись',
        max_length=200,
        blank=True,
        help_text='Необязательно. Отображается поверх изображения.',
    )
    order = models.PositiveIntegerField(
        'Порядок',
        default=0,
        db_index=True,
        help_text='Чем меньше число — тем раньше показывается слайд',
    )
    is_active = models.BooleanField(
        'Активно',
        default=True,
        help_text='Снимите галочку, чтобы временно скрыть слайд',
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Изображение карусели'
        verbose_name_plural = 'Карусель'
        ordering = ['order', 'id']

    def __str__(self):
        return self.title or f'Слайд #{self.pk}'