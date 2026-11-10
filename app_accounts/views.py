"""
Views приложения accounts.

Назначение:
  - login_view: ввод телефона → проверка лимитов → запрос в 1С → отправка SMS.
  - verify_code_view: ввод SMS-кода → проверка → создание User+Profile → логин.
  - dashboard_view: личный кабинет (открытые билеты из 1С).
  - closed_tickets_view: закрытые билеты с пагинацией.
  - logout_view: выход (POST).

Принципы:
  - Телефон НЕ хранится в БД. Только в сессии на время входа.
  - Финансовые данные НЕ кэшируются. Каждый заход в кабинет — живой запрос в 1С.
  - При недоступности 1С — «Данные временно недоступны, попробуйте позже».
  - Логи — без PII (только phone_hash[:8] и id_1c).
"""
import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import PhoneForm, CodeForm
from .models import Profile
from .services.one_c import OneCClient, OneCUnavailable
from .services.sms import get_sms_service, SmsError
from . import utils

logger = logging.getLogger(__name__)

# Ключи сессии (чтобы не хардкодить строки по файлу)
SESSION_PHONE = 'auth_phone'
SESSION_ID_1C = 'auth_id_1c'
SESSION_CONSENT = 'auth_consent'


# ============================================================
# Вспомогательное: создание/получение User+Profile
# ============================================================

def _get_or_create_user(id_1c: str, consent: bool) -> User:
    """
    Возвращает User по id_1c. Создаёт при первом входе.

    - username = UUID (не телефон, не PII).
    - password = unusable (вход только по SMS-коду).
    - Profile.id_1c = GUID из 1С.
    - consent_pd_given/date — из сессии.
    """
    with transaction.atomic():
        profile = (
            Profile.objects
            .select_related('user')
            .filter(id_1c=id_1c)
            .first()
        )

        if profile:
            # Клиент уже заходил — обновляем consent и last_sync
            if consent and not profile.consent_pd_given:
                profile.consent_pd_given = True
                profile.consent_pd_date = timezone.now()
            profile.last_sync_at = timezone.now()
            profile.save(update_fields=[
                'consent_pd_given', 'consent_pd_date', 'last_sync_at',
            ])
            return profile.user

        # Первый вход — создаём
        user = User.objects.create_user(
            username=str(uuid.uuid4()),
            password=None,  # set_unusable_password внутри create_user
        )
        Profile.objects.create(
            user=user,
            id_1c=id_1c,
            consent_pd_given=consent,
            consent_pd_date=timezone.now() if consent else None,
            last_sync_at=timezone.now(),
        )
        return user


def _clear_auth_session(request):
    """Убирает временные ключи входа из сессии."""
    for key in (SESSION_PHONE, SESSION_ID_1C, SESSION_CONSENT):
        request.session.pop(key, None)


def _render_login(request, form):
    """Хелпер: рендер login.html с обязательным privacy_policy_url."""
    return render(request, 'accounts/login.html', {
        'form': form,
        'privacy_policy_url': settings.PRIVACY_POLICY_URL,
    })


# ============================================================
# login_view: ввод телефона
# ============================================================

def login_view(request):
    """
    GET  — показать форму телефона.
    POST — проверить лимиты → 1С → отправить SMS → редирект на verify.
    """
    if request.user.is_authenticated:
        return redirect('app_accounts:dashboard')

    form = PhoneForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        phone = form.cleaned_data['phone']
        consent = form.cleaned_data['consent_pd']

        # 1. Блокировка после N неудачных запросов SMS
        if utils.is_phone_login_blocked(phone):
            messages.error(
                request,
                'Слишком много попыток. Попробуйте позже или обратитесь в филиал.'
            )
            return _render_login(request, form)

        # 2. Лимиты отправки SMS (60 сек, 5/час)
        can_send, reason = utils.can_send_sms(phone)
        if not can_send:
            if reason == 'resend_too_soon':
                messages.warning(request, 'SMS уже отправлено. Подождите минуту.')
            elif reason == 'hour_limit_exceeded':
                messages.error(request, 'Превышен лимит SMS на час. Попробуйте позже.')
            return _render_login(request, form)

        # 3. Проверка в 1С
        client = OneCClient()
        try:
            result = client.check_client_by_phone(phone)
        except OneCUnavailable:
            utils.register_failed_sms_request(phone)
            messages.error(request, 'Данные временно недоступны, попробуйте позже.')
            return _render_login(request, form)

        if not result.found:
            utils.register_failed_sms_request(phone)
            if result.reason == 'ambiguous_phone':
                messages.error(request, 'Обратитесь в наш филиал для уточнения данных.')
            else:
                messages.error(
                    request,
                    'Мы не нашли ваш номер телефона. Обратитесь в наш филиал.'
                )
            return _render_login(request, form)

        # 4. Клиент найден — генерируем и отправляем код
        code = utils.generate_sms_code()
        try:
            get_sms_service().send_code(phone, code)
        except SmsError:
            logger.exception('SMS send failed for hash=%s', utils.hash_phone(phone)[:8])
            messages.error(request, 'Не удалось отправить SMS. Попробуйте позже.')
            return _render_login(request, form)

        # 5. Сохраняем код в Redis и данные в сессию
        utils.set_sms_code(phone, code)
        utils.register_sms_sent(phone)
        utils.reset_failed_sms_requests(phone)  # успех — счётчик неудач сбрасываем

        request.session[SESSION_PHONE] = phone
        request.session[SESSION_ID_1C] = result.id_1c
        request.session[SESSION_CONSENT] = consent

        return redirect('app_accounts:verify_code')

    return _render_login(request, form)


# ============================================================
# verify_code_view: ввод SMS-кода
# ============================================================

def verify_code_view(request):
    """
    GET  — показать форму кода.
    POST — проверить код → создать User+Profile → логин → dashboard.
    """
    phone = request.session.get(SESSION_PHONE)
    id_1c = request.session.get(SESSION_ID_1C)
    consent = request.session.get(SESSION_CONSENT, False)

    # Нет данных входа — вернуть на login
    if not phone or not id_1c:
        return redirect('app_accounts:login')

    if request.user.is_authenticated:
        return redirect('app_accounts:dashboard')

    # Блокировка ввода кода
    if utils.is_code_verify_blocked(phone):
        messages.error(
            request,
            'Слишком много неверных попыток. Попробуйте через 15 минут.'
        )
        _clear_auth_session(request)
        return redirect('app_accounts:login')

    form = CodeForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        entered = form.cleaned_data['code']
        real_code = utils.get_sms_code(phone)

        if not real_code:
            messages.error(request, 'Код истёк. Запросите новый.')
            _clear_auth_session(request)
            return redirect('app_accounts:login')

        if entered != real_code:
            left = utils.get_code_attempts_left(phone) - 1
            utils.register_code_attempt(phone)
            if utils.is_code_verify_blocked(phone):
                messages.error(
                    request,
                    'Слишком много неверных попыток. Попробуйте через 15 минут.'
                )
                _clear_auth_session(request)
                return redirect('app_accounts:login')
            messages.error(request, f'Неверный код. Осталось попыток: {max(left, 0)}.')
            return render(request, 'accounts/verify_code.html', {'form': form})

        # Код верный — создаём/получаем User, логиним
        try:
            user = _get_or_create_user(id_1c, consent)
        except Exception:
            logger.exception('User create failed id_1c=%s', id_1c)
            messages.error(request, 'Ошибка входа. Попробуйте позже.')
            return render(request, 'accounts/verify_code.html', {'form': form})

        utils.clear_sms_code(phone)
        utils.reset_code_attempts(phone)
        _clear_auth_session(request)

        auth_login(request, user)
        return redirect('app_accounts:dashboard')

    return render(request, 'accounts/verify_code.html', {'form': form})


# ============================================================
# dashboard_view: личный кабинет
# ============================================================

@login_required
def dashboard_view(request):
    """
    Личный кабинет: открытые билеты + проценты + график.
    При недоступности 1С — сообщение, без падения.
    """
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, 'Профиль не найден. Обратитесь в поддержку.')
        return redirect('app_accounts:login')

    client = OneCClient()
    tickets = []
    error = None

    try:
        result = client.get_open_tickets(str(profile.id_1c))
        tickets = result.tickets
        # Обновляем last_sync_at
        profile.last_sync_at = timezone.now()
        profile.save(update_fields=['last_sync_at'])
    except OneCUnavailable:
        error = 'Данные временно недоступны, попробуйте позже.'

    return render(request, 'accounts/dashboard.html', {
        'tickets': tickets,
        'error': error,
    })


# ============================================================
# closed_tickets_view: закрытые билеты с пагинацией
# ============================================================

@login_required
def closed_tickets_view(request):
    """
    История закрытых залоговых билетов. Пагинация — 10 на страницу.
    """
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, 'Профиль не найден. Обратитесь в поддержку.')
        return redirect('app_accounts:login')

    try:
        page = int(request.GET.get('page', 1))
        if page < 1:
            page = 1
    except (TypeError, ValueError):
        page = 1

    page_size = 10
    client = OneCClient()
    tickets = []
    total = 0
    error = None

    try:
        result = client.get_closed_tickets(
            str(profile.id_1c), page=page, page_size=page_size
        )
        tickets = result.tickets
        total = result.total
        profile.last_sync_at = timezone.now()
        profile.save(update_fields=['last_sync_at'])
    except OneCUnavailable:
        error = 'Данные временно недоступны, попробуйте позже.'

    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1

    return render(request, 'accounts/closed_tickets.html', {
        'tickets': tickets,
        'error': error,
        'page': page,
        'total': total,
        'total_pages': total_pages,
        'page_size': page_size,
    })


# ============================================================
# logout_view: выход
# ============================================================

@require_POST
def logout_view(request):
    """Выход. Только POST (защита от CSRF-подделки GET-выхода)."""
    auth_logout(request)
    return redirect('index')