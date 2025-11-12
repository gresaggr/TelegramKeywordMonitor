# Полная структура проекта Telegram Keyword Monitor

## 📁 Общая структура

```
telegram-keyword-monitor/
├── backend/                          # Backend FastAPI приложение
│   ├── app/
│   │   ├── api/                      # API endpoints
│   │   │   ├── deps.py               # Зависимости (JWT auth)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py           # Регистрация/логин/профиль
│   │   │       ├── balance.py        # Баланс (заглушка)
│   │   │       └── accounts.py       # CRUD Telegram аккаунтов
│   │   │
│   │   ├── core/                     # Ядро приложения
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Настройки из .env
│   │   │   ├── logger.py             # Логирование
│   │   │   └── security.py           # JWT + bcrypt
│   │   │
│   │   ├── db/                       # База данных
│   │   │   ├── __init__.py
│   │   │   └── session.py            # Async SQLAlchemy session
│   │   │
│   │   ├── models/                   # SQLAlchemy модели
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User model
│   │   │   └── account.py            # TelegramAccount, AccountNotification
│   │   │
│   │   ├── schemas/                  # Pydantic схемы
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # UserCreate, UserResponse, etc
│   │   │   ├── token.py              # Token schema
│   │   │   └── account.py            # TelegramAccount schemas
│   │   │
│   │   ├── services/                 # Бизнес-логика
│   │   │   ├── __init__.py
│   │   │   └── telegram.py           # Telegram Bot уведомления
│   │   │
│   │   ├── telegram/                 # Telegram client logic
│   │   │   ├── __init__.py
│   │   │   └── client_manager.py     # Pyrogram менеджер клиентов
│   │   │
│   │   ├── utils/                    # Утилиты
│   │   │   └── generate-secret-key.py # Генератор SECRET_KEY
│   │   │
│   │   └── main.py                   # FastAPI application
│   │
│   ├── migrations/                   # Alembic миграции
│   │   ├── versions/
│   │   │   ├── 2025_11_04_1515-fee6d4b675ca_initial.py
│   │   │   ├── 2025_11_04_2056-e2ddafb90c4e_add_failure_threshold.py
│   │   │   ├── 2025_11_05_1936-32089671c7f0_add_tg_id_default.py
│   │   │   └── 2025_11_12_1200-4a5b6c7d8e9f_create_telegram_accounts.py
│   │   ├── env.py                    # Alembic environment
│   │   ├── script.py.mako
│   │   └── README
│   │
│   ├── sessions/                     # Telegram сессии (gitignored)
│   │   └── account_*.session         # Создаются автоматически
│   │
│   ├── Dockerfile                    # Docker образ backend
│   ├── requirements.txt              # Python зависимости
│   └── alembic.ini                   # Alembic конфигурация
│
├── frontend/                         # Vue.js frontend
│   ├── js/
│   │   ├── components/
│   │   │   ├── login.js              # Компонент логина
│   │   │   ├── register.js           # Компонент регистрации
│   │   │   ├── account-modal.js      # Модальное окно добавления/редактирования аккаунта
│   │   │   ├── verify-code-modal.js  # Модальное окно верификации кода
│   │   │   └── telegram-dashboard.js # Главный dashboard с аккаунтами
│   │   ├── api.js                    # Axios API клиент
│   │   └── app.js                    # Главное Vue приложение
│   │
│   ├── index.html                    # Главная HTML страница
│   └── styles.css                    # Все стили приложения
│
├── logs/                             # Логи приложения (создается автоматически)
│   └── app.log
│
├── docker-compose.yml                # Docker Compose конфигурация
├── .env                              # Переменные окружения (gitignored)
├── .env.example                      # Пример .env файла
├── .gitignore                        # Git ignore rules
├── Makefile                          # Команды для управления проектом
├── README.md                         # Основная документация
├── QUICKSTART.md                     # Быстрый старт
├── API_EXAMPLES.md                   # Примеры использования API
└── PROJECT_STRUCTURE.md              # Этот файл
```

## 🔧 Ключевые компоненты

### Backend

#### 1. **Аутентификация и авторизация**
- `app/core/security.py` - JWT токены, bcrypt хеширование
- `app/api/deps.py` - Dependency для получения текущего пользователя
- `app/api/v1/auth.py` - Endpoints регистрации/логина

#### 2. **Модели данных**
- `User` - Пользователи системы
- `TelegramAccount` - Telegram аккаунты пользователей
- `AccountNotification` - Уведомления об ошибках

#### 3. **Telegram Integration**
- `app/telegram/client_manager.py` - Основной менеджер:
  - Создание Pyrogram клиентов
  - Обработка авторизации (код, 2FA)
  - Мониторинг сообщений
  - Фильтрация по whitelist/blacklist
  - Пересылка с заменами текста
  - Обработка ошибок

#### 4. **API Endpoints**

**Authentication (`/api/v1/auth/`)**
- `POST /register` - Регистрация
- `POST /login` - Вход
- `GET /me` - Текущий пользователь
- `PATCH /me` - Обновить профиль

**Balance (`/api/v1/balance/`)**
- `GET /` - Получить баланс
- `POST /topup` - Пополнить (заглушка)

**Accounts (`/api/v1/accounts/`)**
- `GET /` - Список аккаунтов
- `POST /` - Создать аккаунт
- `POST /verify-code` - Верифицировать
- `GET /{id}` - Получить аккаунт
- `PATCH /{id}` - Обновить
- `POST /{id}/start` - Запустить
- `POST /{id}/stop` - Остановить
- `DELETE /{id}` - Удалить
- `GET /{id}/notifications` - Уведомления
- `POST /{id}/notifications/{nid}/read` - Пометить

### Frontend

#### Компоненты Vue.js

1. **LoginComponent** (`login.js`)
   - Форма входа
   - Переключение на регистрацию

2. **RegisterComponent** (`register.js`)
   - Форма регистрации
   - Валидация полей

3. **AccountModalComponent** (`account-modal.js`)
   - Создание нового аккаунта
   - Редактирование существующего
   - Форма с:
     - Auth данными (phone, API ID/Hash)
     - Device settings (опционально)
     - Proxy settings (опционально)
     - Monitoring settings (whitelist, blacklist, channels, forward, replacements)

4. **VerifyCodeModalComponent** (`verify-code-modal.js`)
   - Ввод кода из Telegram
   - Ввод 2FA пароля (если нужен)

5. **TelegramDashboardComponent** (`telegram-dashboard.js`)
   - Главная страница после логина
   - Статистика (всего, активных, ошибок)
   - Список аккаунтов
   - Управление аккаунтами (start/stop/edit/delete)
   - Просмотр уведомлений
   - Баланс и пополнение

#### API Client (`api.js`)
Централизованный клиент для всех API запросов с:
- Автоматическим добавлением JWT токена
- Обработкой ошибок
- Методами для всех endpoints

### Database Schema

```sql
-- users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    balance FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    default_telegram_chat_id VARCHAR,
    admin_notification_chat_id VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- telegram_accounts table
CREATE TABLE telegram_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    phone_number VARCHAR NOT NULL,
    api_id VARCHAR NOT NULL,
    api_hash VARCHAR NOT NULL,
    device_model VARCHAR,
    system_version VARCHAR,
    app_version VARCHAR,
    proxy_host VARCHAR,
    proxy_port INTEGER,
    proxy_username VARCHAR,
    proxy_password VARCHAR,
    whitelist_keywords TEXT,  -- JSON array
    blacklist_keywords TEXT,  -- JSON array
    monitored_channels TEXT,  -- JSON array
    forward_to_chat_id VARCHAR,
    replacements TEXT,        -- JSON object
    status VARCHAR,           -- initializing, awaiting_code, awaiting_2fa, active, stopped, error
    is_active BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    last_activity TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- account_notifications table
CREATE TABLE account_notifications (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    error_type VARCHAR,       -- auth_error, network_error, forwarding_error, etc
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔄 Жизненный цикл Telegram аккаунта

1. **Создание** (`POST /accounts/`)
   - Сохранение в БД
   - Инициализация Pyrogram клиента
   - Отправка кода на телефон
   - Статус: `awaiting_code`

2. **Верификация** (`POST /accounts/verify-code`)
   - Ввод кода
   - Проверка 2FA (если нужен)
   - Сохранение сессии в файл
   - Статус: `active`

3. **Мониторинг** (автоматически после верификации)
   - Подключение к Telegram
   - Подписка на каналы
   - Обработка сообщений:
     - Проверка whitelist
     - Проверка blacklist
     - Применение replacements
     - Пересылка сообщения

4. **Остановка** (`POST /accounts/{id}/stop`)
   - Отключение клиента
   - Сохранение сессии
   - Статус: `stopped`

5. **Удаление** (`DELETE /accounts/{id}`)
   - Остановка клиента
   - Удаление файла сессии
   - Удаление из БД

## 🔐 Безопасность

### Хранение данных
- ✅ Пароли: bcrypt hashing
- ✅ JWT токены: HMAC SHA-256
- ✅ API credentials: хранятся в БД, не передаются на frontend
- ✅ Telegram сессии: файлы в защищенной директории
- ✅ Изоляция: каждый пользователь видит только свои данные

### Аутентификация
- JWT токены в HTTP-only headers
- Автоматическое обновление токена на frontend
- Срок жизни токена: 7 дней (настраивается)

## 📊 Потоки данных

### Создание аккаунта
```
Frontend → POST /accounts/ → Backend
  ↓
Backend создает запись в БД
  ↓
Telegram Manager создает Pyrogram клиента
  ↓
Pyrogram отправляет код на телефон
  ↓
Backend возвращает account с status="awaiting_code"
  ↓
Frontend показывает модальное окно верификации
```

### Верификация
```
Frontend → POST /verify-code → Backend
  ↓
Telegram Manager вызывает client.sign_in()
  ↓
Pyrogram сохраняет сессию в файл
  ↓
Backend обновляет status="active"
  ↓
Telegram Manager запускает мониторинг
  ↓
Frontend обновляет список аккаунтов
```

### Мониторинг сообщений
```
Telegram Channel → Новое сообщение
  ↓
Pyrogram event handler получает сообщение
  ↓
Проверка whitelist keywords
  ↓
Проверка blacklist keywords
  ↓
Применение replacements
  ↓
Пересылка в указанный чат
  ↓
Обновление last_activity в БД
```

### Обработка ошибок
```
Ошибка в Telegram Manager
  ↓
Создается AccountNotification в БД
  ↓
Обновляется account.status = "error"
  ↓
Отправляется уведомление в админский канал (если настроен)
  ↓
Frontend показывает badge с количеством непрочитанных
```

## 🚀 Развертывание

### Development
```bash
make init     # Создать .env
make secret-key  # Сгенерировать SECRET_KEY
make up       # Запустить Docker
```

### Production
1. Измените пароли и SECRET_KEY
2. Настройте CORS origins
3. Включите HTTPS
4. Настройте backup БД
5. Настройте мониторинг логов
6. Используйте reverse proxy (nginx)

## 📈 Масштабирование

### Горизонтальное
- Backend: несколько инстансов за load balancer
- Redis: для синхронизации состояния между инстансами
- PostgreSQL: репликация для чтения

### Вертикальное
- Увеличение ресурсов контейнеров
- Оптимизация запросов к БД
- Кеширование частых запросов

## 🔮 Будущие улучшения

1. **WebSocket для real-time updates**
2. **Telegram Bot для управления**
3. **Статистика пересланных сообщений**
4. **Планировщик (время работы аккаунтов)**
5. **Поддержка медиа-файлов**
6. **Экспорт/импорт конфигураций**
7. **API rate limiting**
8. **Метрики и мониторинг (Prometheus/Grafana)**

---

**Вопросы?** См. полную документацию в README.md или создайте issue.
