from aiogram import Dispatcher


def register_all_routers(dp: Dispatcher) -> None:
    from handlers.claude_base import router as claude_router
    from handlers.deploy import router as deploy_router
    from handlers.history import router as history_router
    from handlers.start import router as start_router
    from handlers.tz_builder import router as tz_router
    from handlers.visual import router as visual_router

    dp.include_router(start_router)
    dp.include_router(tz_router)
    dp.include_router(visual_router)
    dp.include_router(deploy_router)
    dp.include_router(claude_router)
    dp.include_router(history_router)
