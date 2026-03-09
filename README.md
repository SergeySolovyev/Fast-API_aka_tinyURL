# BTFL link — URL Shortener API

🔗 **Сервис сокращения ссылок** с аутентификацией, аналитикой и кэшированием.

## 📋 Описание

FastAPI приложение для создания коротких ссылок, аналогичное [tinyURL](https://tinyurl.com) и [bitly](https://bitly.com/). 

### Основные возможности:
- ✅ Создание коротких ссылок (анонимно и для зарегистрированных пользователей)
- ✅ Кастомные alias для ссылок
- ✅ Установка времени жизни ссылок
- ✅ Статистика переходов
- ✅ Поиск ссылок по оригинальному URL
- ✅ Система аутентификации (JWT)
- ✅ Redis кэширование популярных ссылок
- ✅ PostgreSQL для хранения данных
- ✅ Автоматическая очистка истекших ссылок (фоновая задача)
- ✅ Удаление неиспользуемых ссылок (настраиваемый порог N дней)
- ✅ Веб-интерфейс (single-page app)

---

## 🚀 Быстрый старт

### Локальный запуск с Docker Compose

1. **Клонировать репозиторий:**
```bash
git clone https://github.com/SergeySolovyev/Fast-API_aka_tinyURL.git
cd Fast-API_aka_tinyURL
```

2. **Создать .env файл:**
```bash
cp .env.example .env
# Отредактируйте .env и установите SECRET_KEY
```

3. **Запустить с Docker Compose:**
```bash
docker-compose up --build
```

4. **Приложение доступно:**
- API: http://localhost:8000
- Документация: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📚 API Документация

### 🔐 Аутентификация

#### Регистрация пользователя
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword"
}
```

#### Вход (получение JWT токена)
```bash
POST /auth/jwt/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=strongpassword
```

**Ответ:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

---

### 🔗 Работа со ссылками

#### 1. Создание короткой ссылки (POST /links/shorten)
Доступно **всем пользователям** (анонимным и авторизованным).

**Без кастомного alias:**
```bash
POST /links/shorten
Content-Type: application/json

{
  "original_url": "https://www.example.com/very/long/url"
}
```

**С кастомным alias:**
```bash
POST /links/shorten
Content-Type: application/json
Authorization: Bearer <token>

{
  "original_url": "https://www.example.com/article",
  "custom_alias": "my-article"
}
```

**С временем жизни:**
```bash
POST /links/shorten
Content-Type: application/json

{
  "original_url": "https://example.com/temporary",
  "expires_at": "2026-12-31T23:59:59"
}
```

**Ответ:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "short_code": "aBc123",
  "original_url": "https://www.example.com/very/long/url",
  "short_url": "http://localhost:8000/aBc123",
  "custom_alias": null,
  "created_at": "2026-03-07T10:00:00",
  "expires_at": null,
  "click_count": 0
}
```

---

#### 2. Переход по короткой ссылке (GET /{short_code})
```bash
GET /aBc123
```
Автоматически перенаправляет на оригинальный URL (HTTP 307).

- ✅ Кэшируется в Redis на 60 секунд
- ✅ Инкрементирует счетчик переходов
- ✅ Проверяет срок действия

---

#### 3. Статистика по ссылке (GET /links/{short_code}/stats)
```bash
GET /links/aBc123/stats
```

**Ответ:**
```json
{
  "short_code": "aBc123",
  "original_url": "https://www.example.com/article",
  "created_at": "2026-03-07T10:00:00",
  "expires_at": null,
  "click_count": 42,
  "last_used_at": "2026-03-07T15:30:00",
  "category": null
}
```

- ✅ Кэшируется на 30 секунд

---

#### 4. Удаление ссылки (DELETE /links/{short_code})
Только для **авторизованных** пользователей. Можно удалять только свои ссылки.

```bash
DELETE /links/aBc123
Authorization: Bearer <token>
```

**Ответ:** HTTP 204 No Content

---

#### 5. Обновление ссылки (PUT /links/{short_code})
Только для **авторизованных** пользователей.

```bash
PUT /links/aBc123
Authorization: Bearer <token>
Content-Type: application/json

{
  "original_url": "https://new-url.com",
  "expires_at": "2027-01-01T00:00:00"
}
```

---

#### 6. Поиск ссылки по URL (GET /links/search/by-url)
```bash
GET /links/search/by-url?original_url=https://www.example.com/article
```

**Ответ:** массив ссылок с таким же original_url

---

### 📊 Дополнительные функции

#### 7. Мои ссылки (GET /links/user/my-links)
Список всех ссылок текущего пользователя.

```bash
GET /links/user/my-links
Authorization: Bearer <token>
```

---

## 🗄️ Структура базы данных

### Таблица `users`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | Primary key |
| email | String | Уникальный email |
| hashed_password | String | Хэш пароля |
| registered_at | Timestamp | Дата регистрации |
| is_active | Boolean | Активен ли пользователь |
| is_superuser | Boolean | Суперпользователь |
| is_verified | Boolean | Верифицирован ли email |

### Таблица `links`
| Поле | Тип | Описание |
|------|-----|----------|
| id | UUID | Primary key |
| short_code | String(50) | Короткий код (уникальный, индексируется) |
| original_url | String(2048) | Оригинальный URL |
| custom_alias | String(50) | Пользовательский alias (опционально) |
| user_id | UUID | FK на users (NULL для анонимов) |
| created_at | Timestamp | Дата создания |
| expires_at | Timestamp | Срок действия (опционально) |
| last_used_at | Timestamp | Последнее использование |
| click_count | Integer | Счетчик переходов |
| category | String(100) | Категория (опционально) |

**Индексы:**
- `short_code` (уникальный)
- `custom_alias` (уникальный)
- `original_url`
- `user_id`
- Составной индекс `(user_id, created_at)`

---

## 🛠️ Технологический стек

- **FastAPI** 0.115+ — веб-фреймворк
- **SQLAlchemy** 2.0+ — ORM
- **PostgreSQL** 16 — основная БД
- **Redis** 7 — кэширование
- **Alembic** — миграции БД
- **fastapi-users** — готовая система аутентификации
- **redis** (asyncio) — кэширование через собственный модуль `cache.py`
- **Pydantic** — валидация данных
- **asyncpg** — асинхронный драйвер PostgreSQL
- **Docker & Docker Compose** — контейнеризация

---

## 🧪 Примеры использования

### Сценарий 1: Анонимное создание ссылки
```bash
# Создать короткую ссылку
curl -X POST http://localhost:8000/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com/SergeySolovyev"}'

# Ответ: {"short_code": "xY7k2p", "short_url": "http://localhost:8000/xY7k2p", ...}

# Перейти по ссылке
curl -L http://localhost:8000/xY7k2p

# Посмотреть статистику
curl http://localhost:8000/links/xY7k2p/stats
```

### Сценарий 2: Создание кастомной ссылки с аутентификацией
```bash
# Зарегистрироваться
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "test1234"}'

# Войти
TOKEN=$(curl -X POST http://localhost:8000/auth/jwt/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=test1234" | jq -r .access_token)

# Создать ссылку с кастомным alias
curl -X POST http://localhost:8000/links/shorten \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://github.com", "custom_alias": "github"}'

# Теперь доступна: http://localhost:8000/github
```

---

## 🔧 Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|--------------|
| `DB_HOST` | Хост PostgreSQL | localhost |
| `DB_PORT` | Порт PostgreSQL | 5432 |
| `DB_NAME` | Имя БД | url_shortener |
| `DB_USER` | Пользователь БД | postgres |
| `DB_PASS` | Пароль БД | postgres |
| `REDIS_HOST` | Хост Redis | localhost |
| `REDIS_PORT` | Порт Redis | 6379 |
| `SECRET_KEY` | Секретный ключ для JWT | (обязательно изменить!) |
| `BASE_URL` | Базовый URL приложения | http://localhost:8000 |

---

## 📦 Развертывание на Render.com

### 1. Создайте PostgreSQL базу
В Render Dashboard:
- New → PostgreSQL
- Скопируйте `Internal Database URL`

### 2. Создайте Redis (Key Value)
- New → Key Value Store
- Скопируйте `Internal Redis URL`

### 3. Создайте Web Service
- New → Web Service
- Подключите GitHub репозиторий
- Runtime: **Python 3**
- Build Command: `pip install -r requirements.txt`
- Start Command: `sh -c "alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port $PORT"`

### 4. Environment Variables
Добавьте в Web Service:
```
DATABASE_URL=<postgres_internal_url>
REDIS_URL=<redis_internal_url>
SECRET_KEY=<ваш_секретный_ключ>
BASE_URL=https://ваш-сервис.onrender.com
```

---

## 📁 Структура проекта

```
.
├── src/
│   ├── auth/                   # Модуль аутентификации
│   │   ├── models.py          # Модель User
│   │   ├── schemas.py         # Pydantic схемы
│   │   └── users.py           # Настройка fastapi-users
│   ├── links/                  # Модуль ссылок
│   │   ├── models.py          # Модель Link
│   │   ├── schemas.py         # Pydantic схемы
│   │   ├── service.py         # Бизнес-логика
│   │   └── router.py          # API endpoints
│   ├── redirect/               # Модуль переадресации
│   │   └── router.py          # Endpoint для /{short_code}
│   ├── config.py              # Конфигурация
│   ├── database.py            # Подключение к БД
│   └── main.py                # Точка входа FastAPI
├── migrations/                 # Alembic миграции
│   ├── versions/
│   │   └── 001_database_creation.py
│   └── env.py
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── .env.example
├── .gitignore
└── README.md
```

---

## 👨‍💻 Автор

Sergey Solovyev  
GitHub: [SergeySolovyev](https://github.com/SergeySolovyev)

---

## 📄 Лицензия

MIT License
