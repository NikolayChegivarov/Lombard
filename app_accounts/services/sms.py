"""
Сервис отправки SMS.

Назначение:
  - Абстракция над SMS-провайдером. Views и utils НЕ знают, кто именно
    отправляет SMS (SMS.ru, SMS Aero, Twilio, 1С-шлюз...).
  - Сейчас — StubSmsService: пишет код в лог (для разработки).
  - Когда выберете провайдера — добавите класс-наследник BaseSmsService,
    фабрика get_sms_service() начнёт возвращать его. Код views не меняется.

Принципы:
  - Телефон НЕ логируем. Только phone_hash[:8] для отладки.
  - Любая ошибка провайдера → SmsError. View покажет «Не удалось отправить
    SMS, попробуйте позже».
  - Один метод send_code(phone, code) — шлём только код, ничего лишнего.

Использование:
    from app_accounts.services.sms import get_sms_service, SmsError

    sms = get_sms_service()
    try:
        sms.send_code(phone, code)
    except SmsError:
        # показать «Не удалось отправить SMS, попробуйте позже»
        ...
"""
import logging
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================================
# Исключения
# ============================================================

class SmsError(Exception):
    """Ошибка отправки SMS (провайдер недоступен, вернул ошибку и т.п.)."""


# ============================================================
# Базовый интерфейс
# ============================================================

class BaseSmsService(ABC):
    """
    Абстрактный сервис отправки SMS.
    Все реализации обязаны иметь метод send_code.
    """

    @abstractmethod
    def send_code(self, phone: str, code: str) -> None:
        """
        Отправляет SMS-код на указанный телефон.

        :param phone: номер телефона (в любом формате — нормализация внутри)
        :param code: 6-значный код
        :raises SmsError: если отправка не удалась
        """
        raise NotImplementedError


# ============================================================
# Stub: для разработки (пишет код в лог)
# ============================================================

class StubSmsService(BaseSmsService):
    """
    Заглушка для разработки: не отправляет SMS, а пишет код в лог.
    Позволяет протестировать весь поток входа без реального провайдера.

    В логе будет: SMS to hash:da3cc66e code=123456
    Телефон в открытом виде — НЕ пишется (только хеш).
    """

    def send_code(self, phone: str, code: str) -> None:
        from app_accounts.utils import hash_phone

        phone_hash = hash_phone(phone)[:8]
        logger.info('SMS (stub) to hash:%s code=%s', phone_hash, code)
        # Намеренно не бросаем исключение — стаб всегда «успешен».


# ============================================================
# Фабрика
# ============================================================

def get_sms_service() -> BaseSmsService:
    """
    Возвращает экземпляр SMS-сервиса по settings.SMS_PROVIDER.

    Сейчас поддерживается только 'stub'. Когда добавите провайдера
    (например, 'smsru'), допишите ветку в match/if — views не меняются.
    """
    provider = (settings.SMS_PROVIDER or 'stub').lower()

    if provider == 'stub':
        return StubSmsService()

    # --- Пример на будущее ---
    # if provider == 'smsru':
    #     from .sms_providers.smsru import SmsRuService
    #     return SmsRuService(api_key=settings.SMS_API_KEY, sender=settings.SMS_SENDER)
    #
    # if provider == 'smsaero':
    #     from .sms_providers.smsaero import SmsAeroService
    #     return SmsAeroService(api_key=settings.SMS_API_KEY, sender=settings.SMS_SENDER)

    logger.error('Unknown SMS_PROVIDER: %r — falling back to stub', provider)
    return StubSmsService()