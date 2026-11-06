# ==============================================================================
# ИМПОРТЫ
# ==============================================================================

from pathlib import Path                # Удобная работа с путями файловой системы
import os                               # Доступ к переменным окружения и путям
from dotenv import load_dotenv          # Загрузка переменных из .env файла

# Загружаем переменные окружения из файла .env (SECRET_KEY, данные БД и т.д.)
load_dotenv()


# ==============================================================================
# БАЗОВЫЕ ПУТИ
# ==============================================================================

# BASE_DIR — корневая директория проекта (на уровень выше файла settings.py).
# Используется для построения всех остальных путей внутри проекта.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# БЕЗОПАСНОСТЬ
# ==============================================================================

# Секретный ключ берётся из переменной окружения.
# ВАЖНО: никогда не храните ключ в коде и не коммитьте его в репозиторий.
SECRET_KEY = os.getenv('SECRET_KEY', '')

# API-ключ для Яндекс.Карт (JavaScript API и HTTP Геокодер)
# Получить: https://developer.tech.yandex.ru/services/
# Пока пусто — карта работает в бесплатном режиме с водяным знаком
API_KEY_YANDEX_MAP = os.getenv('API_KEY_YANDEX_MAP', '')

# Режим отладки. True — для разработки, False — для продакшена.
# Значение берётся из .env: DEBUG=True / DEBUG=False
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Список хостов, с которых разрешено обращаться к приложению.
ALLOWED_HOSTS = [
    '155.212.145.156',   # IP сервера
    'localhost',         # Локальный хост
    '127.0.0.1',         # Локальный IPv4
    '[::1]',             # Локальный IPv6
    'testserver'
]

# Доверенные источники для CSRF (нужно на проде с HTTPS).
# Пример: CSRF_TRUSTED_ORIGINS = ['https://lombard-narodnyi.ru']
# Пока закомментировано — включим на сервере.
# CSRF_TRUSTED_ORIGINS = []


# ==============================================================================
# ПРИЛОЖЕНИЯ (INSTALLED_APPS)
# ==============================================================================

INSTALLED_APPS = [
    # --- Стандартные приложения Django ---
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # --- Пользовательские приложения проекта ---
    'app_core',
    'app_branches',
    'app_accounts',
    'app_common',
    'app_prices',
    'app_analytics',
    'app_carousel',
]


# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==============================================================================
# URL И ШАБЛОНЫ
# ==============================================================================

ROOT_URLCONF = 'project_lombard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app_branches.context_processors.city_context',
                'app_common.context_processors.news_context',
            ],
        },
    },
]


# ==============================================================================
# WSGI / ASGI
# ==============================================================================

WSGI_APPLICATION = 'project_lombard.wsgi.application'


# ==============================================================================
# БАЗА ДАННЫХ
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("NAME_DB"),
        'HOST': os.getenv('HOST_DB'),
        'PORT': os.getenv('PORT_DB'),
        'USER': os.getenv('USER_DB'),
        'PASSWORD': os.getenv('PASSWORD_DB'),
    }
}


# ==============================================================================
# АУТЕНТИФИКАЦИЯ
# ==============================================================================

# Используем стандартную модель User из django.contrib.auth.
AUTH_USER_MODEL = 'auth.User'

# Бэкенды аутентификации. Пока стандартный.
# Позже, если понадобится кастомный (вход по телефону), добавим сюда
# 'app_accounts.backends.OneCBackend'.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Куда редиректить неавторизованных при @login_required
LOGIN_URL = '/account/login/'

# Куда редиректить после успешного входа
LOGIN_REDIRECT_URL = '/account/'

# Куда редиректить после выхода
LOGOUT_REDIRECT_URL = '/'


# ==============================================================================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ==============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==============================================================================
# ЛОКАЛИЗАЦИЯ И ЧАСОВОЙ ПОЯС
# ==============================================================================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# СТАТИЧЕСКИЕ И МЕДИА-ФАЙЛЫ
# ==============================================================================

# --- Статика ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --- Медиа ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==============================================================================
# REDIS
# ==============================================================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
REDIS_KEY_PREFIX = os.getenv('REDIS_KEY_PREFIX', 'lombard')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 2,
            'SOCKET_TIMEOUT': 2,
            'IGNORE_EXCEPTIONS': True,
        },
        'KEY_PREFIX': REDIS_KEY_PREFIX,
        'TIMEOUT': 300,
    }
}


# ==============================================================================
# ИНТЕГРАЦИЯ С 1С
# ==============================================================================

# Базовый URL HTTP-сервиса 1С (например, https://1c.example.ru/api)
ONEC_URL = os.getenv('ONEC_URL', '')

# Bearer-токен для авторизации в 1С (выдаёт 1С-ник)
ONEC_TOKEN = os.getenv('ONEC_TOKEN', '')

# Таймауты запросов к 1С (секунды)
ONEC_TIMEOUT_CONNECT = int(os.getenv('ONEC_TIMEOUT_CONNECT', 5))
ONEC_TIMEOUT_READ = int(os.getenv('ONEC_TIMEOUT_READ', 10))


# ==============================================================================
# SMS
# ==============================================================================

# Провайдер: stub | smsru | smsaero | ...
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'stub')
SMS_API_KEY = os.getenv('SMS_API_KEY', '')
SMS_SENDER = os.getenv('SMS_SENDER', '')

# Время жизни SMS-кода (секунды)
SMS_CODE_TTL_SECONDS = int(os.getenv('SMS_CODE_TTL_SECONDS', 300))

# Интервал между отправками на один номер (секунды)
SMS_RESEND_INTERVAL_SECONDS = int(os.getenv('SMS_RESEND_INTERVAL_SECONDS', 60))

# Лимит отправок SMS на номер в час
SMS_MAX_PER_HOUR = int(os.getenv('SMS_MAX_PER_HOUR', 5))


# ==============================================================================
# ЛИМИТЫ ВХОДА И БЛОКИРОВКИ
# ==============================================================================

# Попытки ввода SMS-кода до блокировки
SMS_CODE_MAX_ATTEMPTS = int(os.getenv('SMS_CODE_MAX_ATTEMPTS', 3))

# Длительность блокировки ввода кода (минуты)
SMS_CODE_BLOCK_MINUTES = int(os.getenv('SMS_CODE_BLOCK_MINUTES', 15))

# Неудачные запросы SMS (1С не нашла клиента) до блокировки
LOGIN_MAX_FAILED_SMS_REQUESTS = int(os.getenv('LOGIN_MAX_FAILED_SMS_REQUESTS', 10))

# Длительность блокировки входа (минуты)
LOGIN_BLOCK_MINUTES = int(os.getenv('LOGIN_BLOCK_MINUTES', 25))


# ==============================================================================
# СЕССИЯ
# ==============================================================================

# Время жизни сессии — 30 минут (по ТЗ)
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', 1800))

# Продлевать сессию при каждом запросе (активность пользователя)
SESSION_SAVE_EVERY_REQUEST = True


# ==============================================================================
# ПРОЧЕЕ
# ==============================================================================

# URL политики обработки персональных данных
# (страница создаётся в app_core, сюда выносим для переиспользования в шаблонах)
PRIVACY_POLICY_URL = os.getenv('PRIVACY_POLICY_URL', '/privacy-policy/')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==============================================================================
# ЛОГИРОВАНИЕ
# ==============================================================================

# Папка для логов (создаётся рядом с manage.py)
LOG_DIR = BASE_DIR / 'logs'

# Создаём папку, если её нет (чтобы FileHandler не падал при старте)
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },

    'handlers': {
        # Общий лог всех ошибок проекта
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # Ошибки интеграции с 1С
        'file_1c': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / '1c_errors.log',
            'maxBytes': 5 * 1024 * 1024,   # 5 МБ
            'backupCount': 5,               # храним 5 файлов
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        # Ошибки SMS
        'file_sms': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'sms_errors.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },

    'loggers': {
        # Логгер интеграции с 1С (app_accounts.services.one_c)
        'app_accounts.services.one_c': {
            'handlers': ['console', 'file_1c'],
            'level': 'INFO',
            'propagate': False,
        },
        # Логгер SMS (app_accounts.services.sms)
        'app_accounts.services.sms': {
            'handlers': ['console', 'file_sms'],
            'level': 'INFO',
            'propagate': False,
        },
        # Логгер utils (лимиты, блокировки)
        'app_accounts.utils': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Корневой логгер — всё остальное
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}