.PHONY: help build up down restart logs clean migrate shell test

help:
	@echo "Telegram Keyword Monitor - Доступные команды:"
	@echo ""
	@echo "  make init           - Первичная инициализация проекта"
	@echo "  make build          - Собрать Docker образы"
	@echo "  make up             - Запустить все сервисы"
	@echo "  make down           - Остановить все сервисы"
	@echo "  make restart        - Перезапустить сервисы"
	@echo "  make rebuild        - Пересобрать и запустить"
	@echo "  make logs           - Просмотр логов"
	@echo "  make logs-backend   - Просмотр логов backend"
	@echo "  make logs-frontend  - Просмотр логов frontend"
	@echo "  make migrate        - Применить миграции"
	@echo "  make migrate-create - Создать новую миграцию"
	@echo "  make shell          - Войти в backend контейнер"
	@echo "  make db-shell       - Войти в PostgreSQL"
	@echo "  make clean          - Полная очистка (включая volumes)"
	@echo "  make secret-key     - Сгенерировать SECRET_KEY"

init:
	@echo "Инициализация проекта..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Создан .env файл из .env.example"; \
		echo "⚠ ВАЖНО: Отредактируйте .env и запустите 'make secret-key'"; \
	else \
		echo "✓ .env файл уже существует"; \
	fi
	@mkdir -p logs backend/sessions
	@echo "✓ Созданы необходимые директории"
	@echo ""
	@echo "Следующие шаги:"
	@echo "1. Отредактируйте .env файл"
	@echo "2. Запустите: make secret-key"
	@echo "3. Вставьте сгенерированный ключ в .env"
	@echo "4. Запустите: make up"

secret-key:
	@echo "Генерация SECRET_KEY..."
	@python3 backend/app/utils/generate-secret-key.py

build:
	@echo "Сборка Docker образов..."
	docker-compose build

up:
	@echo "Запуск сервисов..."
	docker-compose up -d
	@echo ""
	@echo "✓ Сервисы запущены!"
	@echo "Frontend: http://localhost:8080"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Применение миграций..."
	@sleep 5
	@make migrate

down:
	@echo "Остановка сервисов..."
	docker-compose down

restart:
	@echo "Перезапуск сервисов..."
	docker-compose restart

rebuild:
	@echo "Пересборка и запуск..."
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo ""
	@echo "✓ Сервисы пересобраны и запущены!"
	@sleep 5
	@make migrate

logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

migrate:
	@echo "Применение миграций..."
	docker-compose exec backend alembic upgrade head
	@echo "✓ Миграции применены"

migrate-create:
	@read -p "Введите описание миграции: " desc; \
	docker-compose exec backend alembic revision --autogenerate -m "$$desc"

shell:
	@echo "Вход в backend контейнер..."
	docker-compose exec backend /bin/bash

db-shell:
	@echo "Вход в PostgreSQL..."
	docker-compose exec postgres psql -U postgres -d telegram_monitor

clean:
	@echo "⚠ ВНИМАНИЕ: Это удалит ВСЕ данные, включая базу данных и сессии!"
	@read -p "Продолжить? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v; \
		rm -rf logs/* backend/sessions/*.session; \
		echo "✓ Полная очистка выполнена"; \
	else \
		echo "Отменено"; \
	fi

test:
	@echo "Проверка статуса сервисов..."
	@echo ""
	@echo "Backend:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend недоступен"
	@echo ""
	@echo "Frontend:"
	@curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8080 || echo "❌ Frontend недоступен"
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec postgres pg_isready -U postgres || echo "❌ PostgreSQL недоступен"
	@echo ""
	@echo "Redis:"
	@docker-compose exec redis redis-cli ping || echo "❌ Redis недоступен"