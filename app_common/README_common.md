# app_common — Общие страницы сайта

Приложение `app_common` содержит «мелкие» информационные страницы ломбарда,
которые не заслуживают отдельного Django-приложения: условия сотрудничества,
новости, вопросы и ответы, контакты, «О нас». Также здесь хранится модель
новостей и логика их отображения.

---

## 📌 Назначение

| Страница | URL | Шаблон |
|---|---|---|
| Условия сотрудничества | `/conditions/` | `conditions.html` |
| Новости | `/news/` | `news.html` |
| Вопросы и ответы (FAQ) | `/questions-answers/` | `questions_answers.html` |
| Контакты | `/contacts/` | `contacts.html` |
| О нас | `/about-us/` | `about_us.html` |

Все страницы наследуются от базового шаблона `app_core/templates/base/base.html`
и используют единую минималистичную стилистику сайта:
чёрный текст, белый фон, красный акцент `#e30613` (цвет логотипа).

---

## 🗂️ Структура

```
app_common/
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py            # создаёт таблицу News
├── templates/
│   ├── __init__.py
│   ├── about_us.html              # страница «О нас»
│   ├── conditions.html            # условия сотрудничества
│   ├── contacts.html              # контакты
│   ├── news.html                  # список новостей
│   └── questions_answers.html     # FAQ-аккордеон
├── __init__.py
├── admin.py                       # регистрация модели News в админке
├── apps.py
├── context_processors.py          # флаг has_news для меню (см. ниже)
├── models.py                      # модель News
├── tests.py
├── urls.py                        # маршруты приложения
└── views.py                       # контроллеры страниц
```

---

## 🧠 Модель `News`

Единственная модель приложения — новость.

```python
class News(models.Model):
    title        = CharField(max_length=200)          # заголовок
    text         = TextField()                        # текст новости
    published_at = DateTimeField(default=timezone.now) # дата публикации
    is_published = BooleanField(default=True)         # флаг «опубликовано»
    created_at   = DateTimeField(auto_now_add=True)   # служебное
    updated_at   = DateTimeField(auto_now=True)       # служебное
```

### Особенности модели

- **`published_at` отдельно от `created_at`** — позволяет указать дату
  публикации вручную (например, новость написана сегодня, а датируется вчерашним
  числом). На сайте отображается именно `published_at`.
- **`is_published`** — «черновик». Снимите галочку в админке, и новость
  исчезнет с сайта, оставаясь в базе. Удобно готовить материалы заранее.
- **`Meta.ordering = ['-published_at']`** — сортировка на уровне БД:
  самые свежие новости всегда сверху. На странице `/news/` дополнительная
  сортировка не нужна.
- **`get_short_date()`** — метод возвращает дату в формате `ДД.ММ.ГГГГ`
  для шаблона.

---

## 👀 Views

Все страницы, кроме «О нас» и «Новостей», — простой `render()` без контекста:

```python
def conditions_view(request):
    return render(request, 'conditions.html')

def questions_view(request):
    return render(request, 'questions_answers.html')

def contacts_view(request):
    return render(request, 'contacts.html')
```

### `news_view`

```python
def news_view(request):
    news_list = News.objects.filter(is_published=True)
    return render(request, 'news.html', {'news_list': news_list})
```

- Показывает **только опубликованные** новости.
- Сортировка берётся из `Meta.ordering`.
- Если новостей нет — в шаблоне выводится заглушка
  «Пока новостей нет».

### `about_us_view`

```python
def about_us_view(request):
    active_branches_count = Branch.objects.filter(is_active=True).count()
    return render(request, 'about_us.html', {
        'active_branches_count': active_branches_count,
    })
```

Передаёт в шаблон количество активных филиалов для блока статистики
(анимированный счётчик «N+ филиалов по России»).

> 💡 `active_branches_count` также добавлен в общий
> `app_branches.context_processors.city_context`, поэтому переменная
> доступна на всех страницах. Передача через view — на случай, если
> context processor отключён.

---

## 🧩 Context processor `has_news`

Чтобы пункт «Новости» в выпадающем меню не отображался, пока новостей
нет, используется флаг `has_news`.

```python
# app_common/context_processors.py
from .models import News

def news_context(request):
    return {
        'has_news': News.objects.filter(is_published=True).exists(),
    }
```

Подключение в `settings.py`:

```python
'context_processors': [
    ...
    'app_branches.context_processors.city_context',
    'app_common.context_processors.news_context',  # ← добавить
],
```

В `base.html` пункт меню обёрнут в условие:

```html
{% if has_news %}
<a href="{% url 'app_common:news' %}" class="menu-dropdown__item" role="menuitem">
    Новости
</a>
{% endif %}
```

**Поведение:**
- Есть хотя бы одна опубликованная новость → пункт виден.
- Все новости удалены или сняты с публикации → пункт скрыт,
  остальные четыре пункта меню остаются на месте.

---

## 🛠️ Админка

Новости регистрируются через `NewsAdmin` в `admin.py`:

- Список с колонками: **заголовок**, **дата публикации**,
  **опубликовано**, **создано**.
- Фильтры: по статусу публикации, по дате.
- Поиск по заголовку и тексту.
- Иерархия по дате (`date_hierarchy`).
- Поля разбиты на секции **«Основное»** и **«Публикация»**
  с подсказкой про галочку «Опубликовано».

Раздел в админке: **«Новости»** (`/admin/app_common/news/`).

---

## 🎨 Шаблоны

Все шаблоны используют единый минималистичный стиль сайта:

- `max-width: 820px`, центрирование, отступы 40px / 60px;
- шрифты чёрные (`#000000`);
- красный акцент `#e30613` — для дат, маркеров списков,
  кнопок, «плюсиков» в FAQ;
- разделители — тонкие линии `#eeeeee`;
- БЭМ-именование классов: `conditions__title`, `contacts__item`,
  `faq__question`, `about__list-item` и т.д.

### `news.html`

- Дата новости — красная, над заголовком.
- Заголовок — чёрный, жирный, крупнее текста.
- Текст — `white-space: pre-line`, поэтому абзацы и переносы строк,
  введённые в админке, сохраняются при выводе.
- Между новостями — разделитель `1px solid #eeeeee`, у последней —
  линии нет.

### `questions_answers.html`

- FAQ-аккордеон на чистом JS: открыт всегда только один вопрос.
- «Плюсик» поворачивается на 45° при открытии (превращается в крестик).
- «Плюсик» красный (`#e30613`) — акцент в стилистике сайта.
- Класс `.is-active` на открытом `faq__item`.

### `conditions.html`

- Раздел «Мы не принимаем в залог» — список с красными чёрточками
  вместо маркеров.

### `contacts.html`

- Подзаголовок с красной нижней полосой (`border-bottom: 2px solid #e30613`).
- Email — красная ссылка.
- Каждый пункт — «лейбл + значение», разделены тонкими линиями.

### `about_us.html`

- Анимированный счётчик филиалов на чистом JS (без библиотек).
- Списки принципов и преимуществ — красные чёрточки вместо маркеров.
- CTA-кнопка «Найти ближайший филиал» ведёт на `/#branches`
  (главная с якорем на секцию филиалов).

---

## 🔗 Маршруты

`app_common/urls.py`:

```python
app_name = 'app_common'

urlpatterns = [
    path('conditions/',        views.conditions_view,  name='conditions'),
    path('news/',              views.news_view,        name='news'),
    path('questions-answers/', views.questions_view,   name='questions'),
    path('contacts/',          views.contacts_view,    name='contacts'),
    path('about-us/',          views.about_us_view,    name='about_us'),
]
```

Подключение в `project_lombard/urls.py`:

```python
path('', include('app_common.urls', namespace='app_common')),
```

В шаблонах ссылки строятся через namespace:

```django
{% url 'app_common:news' %}
{% url 'app_common:contacts' %}
```

---

## ⚙️ Зависимости

| От чего зависит | Зачем |
|---|---|
| `app_core/templates/base/base.html` | базовый шаблон (header, footer, меню) |
| `app_branches.models.Branch` | подсчёт активных филиалов для «О нас» |
| `app_branches.context_processors.city_context` | `selected_city`, `all_cities`, `need_city_confirm`, `active_branches_count` |
| `django.contrib.staticfiles` | статика (`Prozr.png` — логотип) |

---

## ✅ Как добавить новость

1. Зайти в `/admin/`.
2. Раздел **«Новости»** → **«Добавить новость»**.
3. Заполнить:
   - **Заголовок** — короткий, до 200 символов;
   - **Текст** — можно с абзацами (переносы сохранятся на сайте);
   - **Дата публикации** — по умолчанию «сейчас», можно изменить;
   - **Опубликовано** — оставить галочку (иначе будет черновик).
4. Сохранить.
5. Проверить `/news/` и выпадающее меню — пункт «Новости» появится,
   как только есть хотя бы одна опубликованная новость.

---

## 🧪 Тесты

`tests.py` пока пустой. При желании можно покрыть:

- `News.get_short_date()` — формат даты;
- `news_view` — что в контексте только `is_published=True`;
- `has_news` в context processor — `True` / `False` в зависимости от БД.

---

## 📝 Соглашения по коду

- **Классы CSS** — БЭМ: `block__element--modifier`.
- **Акцентный цвет** — только `#e30613` (красный логотипа).
- **Шрифты** — `Arial, sans-serif`, чёрный `#000000`.
- **Отступы** — `margin: 40px auto 60px` у корневого контейнера страницы.
- **Максимальная ширина контента** — `820px` для текстовых страниц,
  `1200px` для страниц с сеткой (главная, филиалы — в других приложениях).
- **Новые страницы** — добавлять в `urls.py` с `name=`, в `views.py` —
  простой `render()`, шаблон — наследник `base/base.html`.