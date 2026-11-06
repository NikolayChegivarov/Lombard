"""
Утилиты для работы с SMS-кодами, лимитами и блокировками.

Все данные — в Redis, с TTL. Телефон в ключах — только в виде SHA-256 хеша
(не PII в открытом виде, соответствует 152-ФЗ).
"""
import hashlib
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# ============================================================
# Хеширование телефона
# ============================================================

def normalize_phone(phone: str) -> str:
    """
    Приводит телефон к единому виду: только цифры.
    '8 (900) 123-45-67' → '89001234567'
    '+7 900 123 45 67'  → '79001234567'
    """
    digits = ''.join(ch for ch in phone if ch.isdigit())
    # Приводим к формату 7XXXXXXXXXX (11 цифр)
    if len(digits) == 10:
        digits = '7' + digits
    elif len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    return digits


def hash_phone(phone: str) -> str:
    """
    SHA-256 от нормализованного телефона.
    Используется как ключ в Redis вместо открытого номера.
    """
    return hashlib.sha256(normalize_phone(phone).encode('utf-8')).hexdigest()


# ============================================================
# Ключи Redis
# ============================================================

def _key(prefix: str, phone_hash: str) -> str:
    """Собирает ключ с общим префиксом. django-redis добавит свои 'lombard:1:'."""
    return f'{prefix}:{phone_hash}'


# ============================================================
# SMS-код
# ============================================================

def generate_sms_code() -> str:
    """6-значный код, криптостойкий генератор."""
    return f'{secrets.randbelow(10**6):06d}'


def set_sms_code(phone: str, code: str) -> None:
    """Сохраняет код с TTL из настроек."""
    cache.set(
        _key('sms:code', hash_phone(phone)),
        code,
        timeout=settings.SMS_CODE_TTL_SECONDS,
    )


def get_sms_code(phone: str) -> str | None:
    """Возвращает код или None, если истёк/не было."""
    return cache.get(_key('sms:code', hash_phone(phone)))


def clear_sms_code(phone: str) -> None:
    """Удаляет код после успешного ввода (одноразовый)."""
    cache.delete(_key('sms:code', hash_phone(phone)))


# ============================================================
# Лимиты отправки SMS
# ============================================================

def can_send_sms(phone: str) -> tuple[bool, str]:
    """
    Проверяет, можно ли отправить SMS.
    Возвращает (ok, причина_отказа).

    Проверки:
      1. Интервал между отправками (60 сек).
      2. Лимит в час (5 SMS).
    """
    phone_hash = hash_phone(phone)

    # Интервал между отправками
    last_sent_key = _key('sms:last_sent', phone_hash)
    if cache.get(last_sent_key):
        return False, 'resend_too_soon'

    # Лимит в час
    hour_key = _key('sms:hour_count', phone_hash)
    count = cache.get(hour_key, 0)
    if count >= settings.SMS_MAX_PER_HOUR:
        return False, 'hour_limit_exceeded'

    return True, ''


def register_sms_sent(phone: str) -> None:
    """Фиксирует факт отправки: ставит интервал + инкремент счётчика."""
    phone_hash = hash_phone(phone)

    # Интервал (60 сек)
    cache.set(
        _key('sms:last_sent', phone_hash),
        True,
        timeout=settings.SMS_RESEND_INTERVAL_SECONDS,
    )

    # Счётчик за час
    hour_key = _key('sms:hour_count', phone_hash)
    count = cache.get(hour_key, 0) + 1
    cache.set(hour_key, count, timeout=3600)


# ============================================================
# Попытки ввода SMS-кода (3 → блок 15 мин)
# ============================================================

def is_code_verify_blocked(phone: str) -> bool:
    """Заблокирован ли ввод кода по этому телефону."""
    return bool(cache.get(_key('sms:verify_blocked', hash_phone(phone))))


def register_code_attempt(phone: str) -> int:
    """
    Инкремент неудачных попыток ввода кода.
    При достижении лимита — ставит блок.
    Возвращает текущее количество попыток.
    """
    phone_hash = hash_phone(phone)
    key = _key('sms:verify_attempts', phone_hash)

    count = cache.get(key, 0) + 1

    if count >= settings.SMS_CODE_MAX_ATTEMPTS:
        # Ставим блок
        cache.set(
            _key('sms:verify_blocked', phone_hash),
            True,
            timeout=settings.SMS_CODE_BLOCK_MINUTES * 60,
        )
        # Счётчик сбрасываем — блок уже стоит
        cache.delete(key)
        logger.warning('SMS code verify blocked for phone_hash=%s', phone_hash[:8])
    else:
        # TTL счётчика = время блока (чтобы «сгорал» вместе с блоком)
        cache.set(key, count, timeout=settings.SMS_CODE_BLOCK_MINUTES * 60)

    return count


def reset_code_attempts(phone: str) -> None:
    """Сбрасывает счётчик попыток (после успешного ввода)."""
    cache.delete(_key('sms:verify_attempts', hash_phone(phone)))


# ============================================================
# Блокировка входа после N неудачных запросов SMS (10 → 25 мин)
# ============================================================

def is_phone_login_blocked(phone: str) -> bool:
    """Заблокирован ли вход по этому телефону (после N неудачных запросов SMS)."""
    return bool(cache.get(_key('login:blocked', hash_phone(phone))))


def register_failed_sms_request(phone: str) -> int:
    """
    Инкремент неудачных запросов SMS (1С не нашла клиента / 1С недоступна).
    При достижении лимита — блок на LOGIN_BLOCK_MINUTES.
    """
    phone_hash = hash_phone(phone)
    key = _key('login:failed_requests', phone_hash)

    count = cache.get(key, 0) + 1

    if count >= settings.LOGIN_MAX_FAILED_SMS_REQUESTS:
        cache.set(
            _key('login:blocked', phone_hash),
            True,
            timeout=settings.LOGIN_BLOCK_MINUTES * 60,
        )
        cache.delete(key)
        logger.warning('Login blocked for phone_hash=%s', phone_hash[:8])
    else:
        cache.set(key, count, timeout=settings.LOGIN_BLOCK_MINUTES * 60)

    return count


def reset_failed_sms_requests(phone: str) -> None:
    """Сбрасывает счётчик неудачных запросов (после успешного входа)."""
    cache.delete(_key('login:failed_requests', hash_phone(phone)))


# ============================================================
# Вспомогательное: текущий лимит попыток (для отображения)
# ============================================================

def get_code_attempts_left(phone: str) -> int:
    """Сколько попыток ввода кода осталось."""
    used = cache.get(_key('sms:verify_attempts', hash_phone(phone)), 0)
    return max(0, settings.SMS_CODE_MAX_ATTEMPTS - used)