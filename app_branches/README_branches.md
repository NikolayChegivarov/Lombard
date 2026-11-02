# app_branches

Приложение для управления **филиалами ломбарда**: их адресами, координатами на карте, режимом работы и отображением на интерактивной карте главной страницы.

---

## 🎯 Для чего это приложение

`app_branches` решает три задачи:

1. **Хранение информации о филиалах** — адрес, телефон, координаты, фото, описание.
2. **Учёт режима работы** — расписание по дням недели, автоматический расчёт статуса «открыт/закрыт».
3. **Отображение филиалов на карте** — API для AJAX-загрузки филиалов выбранного города + сериализация для Яндекс.Карт.

---

## 🗂️ Структура приложения

```
app_branches/
├── migrations/                          # Миграции БД
│   ├── 0001_initial.py                  # Branch, WorkingHours
│   ├── 0002_alter_branch_house.py       # Увеличение max_length у house
│   └── 0003_branch_photo.py             # Поле photo
│
├── management/                          # Кастомные команды Django
│   └── commands/
│       ├── __init__.py
│       └── create_branches.py           # Создание тестовых филиалов
│
├── context_processors.py                # selected_city, all_cities, need_city_confirm, YANDEX_MAPS_API_KEY
├── models.py                            # Branch, WorkingHours
├── views.py                             # set_city_view, branches_api_view, _serialize_branch
├── urls.py                              # API-маршруты
├── admin.py                             # Настройка админки (BranchAdmin, WorkingHoursAdmin)
├── apps.py                              # Конфигурация приложения
├── tests.py                             # Юнит-тесты
└── README.md                            # Этот файл
```

---

## 🧩 Модели

### `Branch` — филиал

| Поле | Тип | Описание |
|---|---|---|
| `city` | CharField(100) | Город |
| `street` | CharField(200) | Улица |
| `house` | CharField(50) | Дом (может содержать корпус, строение) |
| `phone` | CharField(20) | Телефон (валидатор: `+7XXXXXXXXXX` / `8XXXXXXXXXX`) |
| `description` | TextField | Описание (опционально) |
| `photo` | ImageField | Фото филиала (опционально) |
| `latitude`, `longitude` | FloatField | Координаты для карты |
| `is_active` | BooleanField | Активен ли филиал |
| `created_at`, `updated_at` | DateTimeField | Даты создания/обновления |

**Методы:**
- `get_formatted_phone()` — возвращает телефон в формате `+7 (4942) 123-456`
- `get_address()` — «Улица, дом»
- `is_open_now()` — проверяет, открыт ли филиал **прямо сейчас** (учитывает `TIME_ZONE='Europe/Moscow'`)
- `get_working_hours_display()` — многострочное расписание

**Сортировка:** по `city`, затем `street`.

---

### `WorkingHours` — режим работы

| Поле | Тип | Описание |
|---|---|---|
| `branch` | ForeignKey(Branch) | Филиал (CASCADE) |
| `day_of_week` | IntegerField(choices) | 0=Пн, ..., 6=Вс |
| `opening_time` | TimeField | Время открытия |
| `closing_time` | TimeField | Время закрытия |
| `is_closed` | BooleanField | Выходной |

**Ограничения:**
- `unique_together = ['branch', 'day_of_week']` — на один филиал один день недели.
- Валидация в `clean()`: для рабочих дней `opening_time < closing_time`.

---

## 🌐 API (JSON)

### `POST /api/set-city/`

Сохраняет выбранный город в **cookie** (`selected_city` URL-encoded, `city_confirmed=1`).

**Request:**
```http
POST /api/set-city/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: <токен>

city=Москва
```

**Response (200):**
```json
{"ok": true, "city": "Москва"}
```

**Response (404):**
```json
{"ok": false, "error": "Город «Казань» не найден"}
```

---

### `GET /api/branches/?city=Москва`

Возвращает список **активных** филиалов выбранного города с расписанием и статусом.

- Если `?city=` не передан — берётся из cookie `selected_city` (URL-decode).
- Если cookie нет — берётся первый город из БД по алфавиту.

**Response:**
```json
{
  "city": "Москва",
  "branches": [
    {
      "id": 7,
      "city": "Москва",
      "street": "Тверская",
      "house": "12",
      "address": "Тверская, 12",
      "phone": "+7 (495) 100-10-01",
      "formatted_phone": "+7 (495) 100-10-01",
      "description": "Филиал в центре Москвы",
      "latitude": 55.761,
      "longitude": 37.609,
      "photo": null,
      "schedule": [
        {"day": "Понедельник", "time": "10:00–20:00", "is_closed": false},
        ...
      ],
      "is_open_now": true,
      "status_text": "Открыт"
    }
  ]
}
```

**Особенность:** `json_dumps_params={'ensure_ascii': False, 'indent': 2}` — русский текст читаем, JSON с отступами (удобно при отладке в браузере).

---

## 🧠 Context processor

`app_branches/context_processors.py` → функция `city_context(request)`.

Добавляет во **все** шаблоны:

| Переменная | Тип | Описание |
|---|---|---|
| `selected_city` | str \| None | Текущий город (из cookie) |
| `all_cities` | list[str] | Все города с активными филиалами |
| `need_city_confirm` | bool | Показать модалку выбора города? |
| `YANDEX_MAPS_API_KEY` | str | Ключ Яндекс.Карт (может быть пустым) |

**Логика выбора города:**
1. Берём `selected_city` из cookie.
2. `unquote()` — URL-decode.
3. Если пусто или города нет в БД → `all_cities[0]`.
4. `need_city_confirm = True`, если cookie `city_confirmed != '1'`.

Подключён в `project_lombard/settings.py` → `TEMPLATES[0]['OPTIONS']['context_processors']`.

---

## 🗺️ Отображение на карте

Главная страница (`app_core/templates/index.html`) получает:

- `branches_json` — список филиалов выбранного города (из view `app_core.views.base.index`)
- `YANDEX_MAPS_API_KEY` — из context processor

JS на клиенте:
1. Читает `branches_json` через `{{ branches_json|json_script:"branchesData" }}`
2. Инициализирует Яндекс.Карту (`ymaps.ready`)
3. Рисует метки + кластеризатор
4. Показывает список справа
5. Клик по метке / строке → детальная панель + центрирование карты

---

## 🛠️ Management-команда: `create_branches`

Создаёт **тестовые филиалы** (18 штук) для разработки.

```bash
# Создать (идемпотентно — повторный запуск ничего не дублирует)
python manage.py create_branches

# Удалить все филиалы и создать заново
python manage.py create_branches --reset
```

**Города и количество:**
- Кострома — 5
- Москва — 10
- Санкт-Петербург — 3

**Расписание:**
- Кострома: Пн–Пт 09:00–19:00, Сб 10:00–17:00, Вс — выходной
- Москва: Пн–Пт 10:00–20:00, Сб–Вс 10:00–18:00
- СПб: ежедневно 10:00–20:00

---

## 🖥️ Админка

### `BranchAdmin`
- Список: город, улица, дом, телефон, статус, дата
- Фильтры: `is_active`, `city`, `created_at`
- **Inline `WorkingHoursInline`** — редактирование расписания прямо в карточке филиала
- Для **нового** филиала автоматически создаются 7 пустых форм (все дни недели)
- `list_editable = ['is_active']` — быстрое вкл/выкл

### `WorkingHoursAdmin`
- Отдельная админка для расписания (массовое редактирование)
- `list_editable` — время и `is_closed` редактируются прямо в списке

---

## 🍪 Cookie

| Cookie | Значение | Срок | Описание |
|---|---|---|---|
| `selected_city` | URL-encoded («Москва» → `%D0%9C...`) | 1 год | Выбранный город |
| `city_confirmed` | `1` | 1 год | Пользователь подтвердил город |

**Почему URL-encode?** По RFC 6265 cookie должны содержать только ASCII. Кириллица ломает Django Test Client и может вести себя непредсказуемо в браузерах.

---

## 📦 Зависимости

- **Django ≥ 5.0**
- **Pillow** — для `ImageField(photo)`
- **psycopg2** — PostgreSQL
- **Yandex Maps API 2.1** — подключается из шаблона (CDN)

---

## 🧪 Тестирование

```bash
# Проверка через shell (Django Test Client)
python manage.py shell
```

```python
from django.test import Client

client = Client()

# 1. GET без cookie → первый город
print(client.get('/api/branches/').json()['city'])   # Кострома

# 2. POST set-city
resp = client.post('/api/set-city/', {'city': 'Москва'})
print(resp.json())                                    # {'ok': True, 'city': 'Москва'}

# 3. GET с cookie → Москва
print(client.get('/api/branches/').json()['city'])   # Москва
print(len(client.get('/api/branches/').json()['branches']))  # 10

# 4. Ошибка
resp = client.post('/api/set-city/', {'city': 'Казань'})
print(resp.status_code)                               # 404
```

⚠️ Для `Client` нужен `'testserver'` в `ALLOWED_HOSTS` (при `DEBUG=True`).

---

## 🚧 Ограничения и планы

### Сейчас
- ❌ **Нет импорта из XML/JSON** (в планах — загрузка филиалов файлом через админку)
- ❌ **Нет загрузки фото** в тестовых данных (поле есть, но `create_branches` его не заполняет)
- ⚠️ **Маршрут** строится через `yandex.ru/maps/?rtext=~lat,lon` — без ключа API, без промежуточных точек

### В планах
- 📥 Импорт филиалов из **XML / JSON** (management-команда или загрузка через админку)
- 🖼️ Массовая загрузка фото
- 🏙️ Определение города по **IP** (нужен API — `ipapi.com` или `sypexgeo`)
- 📊 Статистика по филиалам (в `app_analytics`)

---

## 📝 Связанные приложения

| Приложение | Связь |
|---|---|
| `app_core` | Главная страница (`index`) → передаёт `branches_json` |
| `app_prices` | `MetalPrice` — раньше был здесь, теперь в `app_prices` |
| `app_analytics` | (планируется) логирование запросов к API |

---

## 👤 Автор

Проект «Ломбард Народный», 2026.