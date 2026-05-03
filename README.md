# VibeMaster AI ⚡

Telegram-бот — личный операционный центр вайб-кодера. Превращает мысли в ТЗ, ТЗ — в код и визуал, обучает работе с Claude Code.

## Возможности

| Режим | Описание |
|-------|----------|
| 📝 Создать ТЗ | Пошаговый 5-шаговый конструктор технических заданий через LLM |
| 🎨 Визуал | Генерация изображений с автоулучшением промпта |
| 📚 База Claude | База знаний по командам и фишкам Claude Code |
| 🚀 Деплой | AI-советник по деплою проектов на Railway/Render/Vercel |
| 📜 /history | Последние 5 сгенерированных ТЗ |

## Быстрый старт

```bash
# 1. Клонировать и перейти в директорию
cd vibemaster

# 2. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Настроить переменные окружения
cp .env.example .env
# Отредактировать .env — добавить токены

# 5. Запустить бота
python bot.py
```

## Переменные окружения

| Переменная | Описание | Обязательная |
|-----------|----------|:---:|
| `TELEGRAM_BOT_TOKEN` | Токен бота от @BotFather | ✅ |
| `OPENROUTER_API_KEY_TEXT` | API ключ OpenRouter для текстовых моделей | ✅ |
| `OPENROUTER_API_KEY_IMAGE` | API ключ OpenRouter для генерации изображений | ✅ |
| `DEFAULT_TEXT_MODEL` | Модель для текста (по умолч. `anthropic/claude-3.5-sonnet`) | — |
| `DEFAULT_IMAGE_MODEL` | Модель для изображений (по умолч. `fal-ai/flux-pro`) | — |
| `WEBHOOK_BASE_URL` | HTTPS-URL для webhook (пусто = long polling) | — |
| `LOG_LEVEL` | Уровень логирования (по умолч. `INFO`) | — |
| `MAX_CONCURRENT_TASKS` | Лимит параллельных генераций изображений | — |

## Деплой на Railway

1. Форкни репозиторий на GitHub
2. Зайди на [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Выбери репозиторий
4. В разделе Variables добавь все переменные из таблицы выше
5. В `WEBHOOK_BASE_URL` укажи URL Railway: `https://<app-name>.railway.app`
6. Railway автоматически задеплоит проект

## Разработка

```bash
# Запустить тесты
pytest tests/ -v

# Линтер
ruff check .

# Авто-исправление
ruff check . --fix
```

## Структура проекта

```
vibemaster/
├── bot.py              # Точка входа
├── config.py           # Настройки (pydantic-settings)
├── handlers/           # Обработчики команд
├── fsm/                # Конечные автоматы
├── services/           # Бизнес-логика (DB, OpenRouter, KB)
├── keyboards/          # Клавиатуры Telegram
├── models/             # Pydantic-схемы
├── data/               # SQLite + JSON база знаний
└── tests/              # Тесты
```

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/cancel` | Отменить текущую операцию |
| `/history` | Последние 5 ТЗ |
| `/image` | Генерация изображения |
| `/reload_kb` | Перезагрузить базу знаний Claude |
| `/help` | Список команд |
