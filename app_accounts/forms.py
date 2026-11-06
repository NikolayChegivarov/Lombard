"""
Формы приложения accounts.

Назначение:
  - PhoneForm: ввод телефона + согласие на обработку ПД.
  - CodeForm: ввод 6-значного SMS-кода.

Принципы:
  - Валидация телефона — через normalize_phone() из utils.py (единый формат).
  - В формах НЕТ логики отправки SMS / запросов в 1С. Только валидация ввода.
    Вся бизнес-логика — во views.
  - Телефон в форме НЕ сохраняется в БД (только в сессии, на время входа).
"""
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator

from .utils import normalize_phone


# ============================================================
# PhoneForm: ввод телефона + согласие на ПД
# ============================================================

class PhoneForm(forms.Form):
    """
    Форма ввода телефона для входа.

    Поля:
      - phone: номер телефона (11 цифр, начинается с 7).
      - consent_pd: галочка согласия на обработку ПД (обязательна).
    """

    phone = forms.CharField(
        label='Номер телефона',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+7 (___) ___-__-__',
            'autocomplete': 'tel',
            'inputmode': 'tel',
            'autofocus': True,
        }),
        validators=[
            RegexValidator(
                regex=r'^[\d\s\(\)\+\-]+$',
                message='Номер может содержать только цифры, пробелы, скобки, «+» и «-».',
            ),
        ],
    )

    consent_pd = forms.BooleanField(
        label='Я согласен с обработкой персональных данных',
        required=True,
        error_messages={
            'required': 'Без согласия на обработку ПД вход невозможен.',
        },
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        }),
    )

    def clean_phone(self) -> str:
        """
        Нормализует телефон к формату 7XXXXXXXXXX (11 цифр).
        Бросает ValidationError, если номер некорректен.
        """
        raw = self.cleaned_data['phone']
        normalized = normalize_phone(raw)

        if len(normalized) != 11 or not normalized.startswith('7'):
            raise forms.ValidationError(
                'Введите корректный номер телефона (11 цифр, например +7 900 123-45-67).'
            )

        return normalized


# ============================================================
# CodeForm: ввод SMS-кода
# ============================================================

class CodeForm(forms.Form):
    """
    Форма ввода 6-значного SMS-кода.

    Поле code — только цифры, ровно 6 символов.
    """

    code = forms.CharField(
        label='Код из SMS',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input form-input--code',
            'placeholder': '______',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric',
            'pattern': r'\d{6}',
            'maxlength': '6',
            'autofocus': True,
        }),
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message='Код состоит из 6 цифр.',
            ),
        ],
    )
