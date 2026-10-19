from django.db import models
from django.utils import timezone


class News(models.Model):
    """Новости ломбарда"""

    id = models.AutoField(primary_key=True, verbose_name='ID')
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст новости')
    published_at = models.DateTimeField(
        default=timezone.now,
        verbose_name='Дата публикации',
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть новость с сайта',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']  # сначала самые свежие

    def __str__(self):
        return self.title

    def get_short_date(self):
        """Дата в формате ДД.ММ.ГГГГ"""
        return self.published_at.strftime('%d.%m.%Y')