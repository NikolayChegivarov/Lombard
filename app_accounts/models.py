from django.conf import settings
from django.db import models


class Profile(models.Model):
    """
    Профиль клиента ломбарда.

    Хранит МИНИМУМ данных:
      - связь с 1С (id_1c — GUID клиента);
      - юридический факт согласия на обработку ПД;
      - служебные даты для аудита.

    НЕ хранит: телефон, ФИО, паспорт, суммы, билеты.
    Всё это — в 1С, запрашивается при каждом входе в кабинет.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь',
    )
    id_1c = models.UUIDField(
        unique=True,
        db_index=True,
        verbose_name='ID клиента в 1С (GUID)',
        help_text='GUID клиента из 1С. Единственное связующее звено с внешней системой. '
                  'Не меняется при смене телефона клиента.',
    )
    consent_pd_given = models.BooleanField(
        default=False,
        verbose_name='Согласие на обработку ПД получено',
    )
    consent_pd_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата согласия на обработку ПД',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания',
    )
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Последняя успешная синхронизация с 1С',
        help_text='Обновляется при каждом успешном запросе к 1С.',
    )

    class Meta:
        verbose_name = 'Профиль клиента'
        verbose_name_plural = 'Профили клиентов'
        ordering = ('-created_at',)

    def __str__(self):
        return f'Профиль {self.user_id} (1C: {self.id_1c})'