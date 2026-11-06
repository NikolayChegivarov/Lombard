"""
Клиент 1С:HTTP-сервиса.

Назначение файла:
  - Единая точка общения с 1С. Все запросы к 1С идут ТОЛЬКО отсюда.
  - Инкапсулирует: адрес, Bearer-токен, таймауты, парсинг JSON, обработку ошибок.
  - Возвращает Python-объекты (dataclass), а не сырой JSON — views не должны
    знать, как выглядит ответ 1С.

Принципы:
  - Никаких финансовых данных не кэшируем и не храним. Каждый запрос — живой.
  - Телефон НЕ логируем. Только phone_hash[:8] для отладки.
  - Любая сетевая/HTTP-ошибка → OneCUnavailable (views покажут
    «Данные временно недоступны, попробуйте позже»).
  - Бизнес-ошибка (клиент не найден, несколько клиентов) → результат с полем
    found=False и reason, без исключения.

Использование:
    from app_accounts.services.one_c import OneCClient, OneCUnavailable

    client = OneCClient()
    try:
        result = client.check_client_by_phone(phone)
    except OneCUnavailable:
        # показать «Данные временно недоступны»
        ...
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================================
# Исключения
# ============================================================

class OneCError(Exception):
    """Базовая ошибка при работе с 1С."""


class OneCUnavailable(OneCError):
    """1С недоступна (сеть, таймаут, 5xx). Views показывают «попробуйте позже»."""


# ============================================================
# Модели результата (dataclass — чтобы views не лазили в JSON)
# ============================================================

@dataclass
class ClientCheckResult:
    """Результат проверки клиента по телефону."""
    found: bool
    id_1c: Optional[str] = None
    reason: str = ''          # not_found | ambiguous_phone | internal_error
    message: str = ''         # текст от 1С (для логов, не для клиента)


@dataclass
class Ticket:
    """Залоговый билет (открытый или закрытый)."""
    ticket_number: str
    status: str                         # 'open' | 'closed'
    issue_date: Optional[date] = None
    close_date: Optional[date] = None
    loan_amount: Optional[Decimal] = None
    collateral_value: Optional[Decimal] = None
    current_debt: Optional[Decimal] = None
    current_percent: Optional[Decimal] = None
    repayment_amount: Optional[Decimal] = None
    payment_schedule: list = field(default_factory=list)


@dataclass
class TicketsResult:
    """Результат запроса билетов (с пагинацией для закрытых)."""
    tickets: list
    total: int = 0
    page: int = 1
    page_size: int = 10


# ============================================================
# Парсеры (JSON → dataclass)
# ============================================================

def _parse_date(value) -> Optional[date]:
    """'2024-01-15' или '2024-01-15T00:00:00' → date. None, если пусто."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def _parse_decimal(value) -> Optional[Decimal]:
    """'15000.00' или 15000.0 → Decimal. None, если пусто/не число."""
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_ticket(raw: dict) -> Ticket:
    """Сырой dict из 1С → Ticket."""
    schedule = []
    for item in raw.get('payment_schedule') or []:
        schedule.append({
            'date': _parse_date(item.get('date')),
            'amount': _parse_decimal(item.get('amount')),
        })
    return Ticket(
        ticket_number=str(raw.get('ticket_number', '')),
        status=str(raw.get('status', '')),
        issue_date=_parse_date(raw.get('issue_date')),
        close_date=_parse_date(raw.get('close_date')),
        loan_amount=_parse_decimal(raw.get('loan_amount')),
        collateral_value=_parse_decimal(raw.get('collateral_value')),
        current_debt=_parse_decimal(raw.get('current_debt')),
        current_percent=_parse_decimal(raw.get('current_percent')),
        repayment_amount=_parse_decimal(raw.get('repayment_amount')),
        payment_schedule=schedule,
    )


# ============================================================
# Клиент 1С
# ============================================================

class OneCClient:
    """
    HTTP-клиент 1С.

    Один экземпляр на запрос (не переиспользуем между запросами — requests.Session
    внутри, но создаётся в __init__; для нашего объёма это нормально).
    """

    def __init__(self):
        self.base_url = settings.ONEC_URL.rstrip('/')
        self.token = settings.ONEC_TOKEN
        self.timeout = (
            settings.ONEC_TIMEOUT_CONNECT,
            settings.ONEC_TIMEOUT_READ,
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
        })

    # ---------- низкоуровневый GET ----------

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        """
        GET-запрос к 1С. Возвращает dict (распарсенный JSON).

        Бросает OneCUnavailable при любой сетевой/HTTP-проблеме.
        """
        url = f'{self.base_url}{path}'
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.Timeout:
            logger.error('1C timeout: path=%s params=%s', path, self._safe_params(params))
            raise OneCUnavailable('1C timeout')
        except requests.exceptions.RequestException as e:
            # ВАЖНО: не логируем str(e) целиком — requests вставляет URL с query-string,
            # где может быть телефон. Логируем только тип исключения и безопасный url без params.
            logger.error(
                '1C connection error: path=%s type=%s url_base=%s',
                path,
                type(e).__name__,
                url,
            )
            raise OneCUnavailable('1C connection error')

    @staticmethod
    def _safe_params(params: Optional[dict]) -> dict:
        """Убирает телефон из params для логов (оставляет только хеш)."""
        if not params:
            return {}
        safe = dict(params)
        if 'phone' in safe:
            # Импорт здесь, чтобы не было циклической зависимости
            from app_accounts.utils import hash_phone
            safe['phone'] = f'hash:{hash_phone(safe["phone"])[:8]}'
        return safe

    # ---------- публичные методы ----------

    def check_client_by_phone(self, phone: str) -> ClientCheckResult:
        """
        Проверяет, есть ли клиент с таким телефоном в 1С.

        Возвращает ClientCheckResult. Не бросает исключений для бизнес-случаев
        (не найден, несколько клиентов). Бросает OneCUnavailable только при
        сетевой/HTTP-проблеме.
        """
        data = self._get('/clients/check-by-phone', params={'phone': phone})

        found = bool(data.get('found'))
        if not found:
            return ClientCheckResult(
                found=False,
                reason=data.get('reason', 'not_found'),
                message=data.get('message', ''),
            )

        client = data.get('client') or {}
        id_1c = client.get('id_1c')
        if not id_1c:
            logger.error('1C returned found=true but no id_1c')
            return ClientCheckResult(found=False, reason='internal_error')

        return ClientCheckResult(found=True, id_1c=str(id_1c))

    def get_open_tickets(self, id_1c: str) -> TicketsResult:
        """Открытые залоговые билеты клиента."""
        data = self._get(f'/clients/{id_1c}/tickets', params={'status': 'open'})
        tickets = [_parse_ticket(t) for t in (data.get('tickets') or [])]
        return TicketsResult(tickets=tickets)

    def get_closed_tickets(self, id_1c: str, page: int = 1, page_size: int = 10) -> TicketsResult:
        """Закрытые билеты с пагинацией."""
        data = self._get(
            f'/clients/{id_1c}/tickets',
            params={'status': 'closed', 'page': page, 'page_size': page_size},
        )
        tickets = [_parse_ticket(t) for t in (data.get('tickets') or [])]
        return TicketsResult(
            tickets=tickets,
            total=int(data.get('total', 0)),
            page=int(data.get('page', page)),
            page_size=int(data.get('page_size', page_size)),
        )