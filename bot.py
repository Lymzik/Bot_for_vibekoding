import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from loguru import logger

from config import settings
from services import knowledge_base
from services.database import init_db

# Настройка логирования
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
    level=settings.log_level,
    colorize=True,
)
logger.add(
    "logs/bot.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    serialize=False,
)


async def on_startup(bot: Bot) -> None:
    await init_db()
    logger.info("База данных инициализирована")
    knowledge_base.load()


    if settings.webhook_base_url:
        webhook_url = f"{settings.webhook_base_url}/webhook/{settings.telegram_bot_token}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret,
        )
        logger.info(f"Webhook установлен: {webhook_url}")
    else:
        logger.info("WEBHOOK_BASE_URL не задан — используется long polling")


async def on_shutdown(bot: Bot) -> None:
    if settings.webhook_base_url:
        await bot.delete_webhook()
    logger.info("Бот остановлен")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Импорт и регистрация роутеров
    from handlers import register_all_routers
    register_all_routers(dp)

    return dp


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    logger.info("Запуск в режиме long polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    logger.info(f"Запуск webhook-сервера на порту {settings.port}...")
    webhook_path = f"/webhook/{settings.telegram_bot_token}"

    app = web.Application()
    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    )
    handler.register(app, path=webhook_path)

    # Health check для Railway
    async def health(request: web.Request) -> web.Response:
        return web.Response(text="OK")

    app.router.add_get("/health", health)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=settings.port)


def main() -> None:
    Path("logs").mkdir(exist_ok=True)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    if settings.webhook_base_url:
        run_webhook(bot, dp)
    else:
        asyncio.run(run_polling(bot, dp))


if __name__ == "__main__":
    main()
