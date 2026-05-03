import asyncio

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message
from loguru import logger

from config import settings
from services import database
from services.openrouter import OpenRouterError, generate_image
from services.prompt_enhancer import enhance_prompt

router = Router()

_semaphore = asyncio.Semaphore(settings.max_concurrent_tasks)


class VisualStates(StatesGroup):
    waiting_prompt = State()


@router.message(F.text == "🎨 Визуал")
@router.message(Command("image"))
async def visual_enter(message: Message, state: FSMContext) -> None:
    await state.set_state(VisualStates.waiting_prompt)
    await message.answer(
        "🎨 <b>Режим генерации изображений</b>\n\n"
        "Опиши, что нужно нарисовать. Я улучшу твой промпт и создам картинку.\n\n"
        "<i>Пример: иконка финтех-приложения в стиле минимализм</i>\n\n"
        "Для отмены — /cancel"
    )


@router.message(VisualStates.waiting_prompt)
async def visual_generate(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, опиши изображение текстом. Для отмены — /cancel.")
        return

    user_prompt = message.text.strip()
    await state.clear()

    thinking_msg = await message.answer("⏳ <b>Генерирую изображение...</b>\n\nУлучшаю промпт и отправляю запрос.")

    async with _semaphore:
        asyncio.create_task(
            _run_image_generation(message, thinking_msg, user_prompt)
        )


async def _run_image_generation(
    message: Message,
    thinking_msg: Message,
    user_prompt: str,
) -> None:
    try:
        enhanced = await enhance_prompt(user_prompt)
        logger.debug(f"Улучшенный промпт: {enhanced[:100]}...")

        await thinking_msg.edit_text(
            "⏳ <b>Генерирую изображение...</b>\n\n"
            "<i>Промпт улучшен, жду результат от модели...</i>"
        )

        image_bytes = await generate_image(enhanced)

        await database.log_generation(
            user_id=message.from_user.id,
            gen_type="image",
            model_used=settings.default_image_model,
            success=True,
        )

        await thinking_msg.delete()
        await message.answer_photo(
            photo=BufferedInputFile(image_bytes, filename="vibemaster_image.png"),
            caption=f"🎨 <b>Готово!</b>\n\n<b>Промпт:</b> <i>{enhanced[:200]}...</i>" if len(enhanced) > 200 else f"🎨 <b>Готово!</b>\n\n<b>Промпт:</b> <i>{enhanced}</i>",
        )
        logger.info(f"Изображение сгенерировано для user_id={message.from_user.id}")

    except OpenRouterError as e:
        await database.log_generation(
            user_id=message.from_user.id,
            gen_type="image",
            model_used=settings.default_image_model,
            success=False,
        )
        logger.error(f"Ошибка генерации изображения: {e}")
        await thinking_msg.edit_text(
            "❗ Не удалось сгенерировать изображение. Сервис перегружен — попробуй через минуту."
        )

    except TimeoutError:
        logger.warning(f"Таймаут генерации изображения для user_id={message.from_user.id}")
        await thinking_msg.edit_text(
            "⏳ Генерация затянулась. Я пришлю результат, как только он будет готов.\n"
            "Можешь продолжать работу — /start для меню."
        )

    except Exception as e:
        logger.error(f"Неожиданная ошибка генерации изображения: {e}")
        await thinking_msg.edit_text(
            "❗ Произошла ошибка при генерации. Попробуй ещё раз."
        )
