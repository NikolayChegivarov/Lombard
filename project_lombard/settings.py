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
SECRET_KEY = os.getenv('SECRET_KEY')

# Режим отладки. True — для разработки, False — для продакшена.
DEBUG = True

# Список хостов, с которых разрешено обращаться к приложению.
ALLOWED_HOSTS = [
    '155.212.145.156',   # IP сервера
    'localhost',         # Локальный хост
    '127.0.0.1',         # Локальный IPv4
    '[::1]',             # Локальный IPv6
]


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

                # 👇 Раскомментируем на Шаге 3, когда создадим файл
                # 'app_branches.context_processors.city_context',
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
# ПРОЧЕЕ
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'