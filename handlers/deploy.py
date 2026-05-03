from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from fsm.deploy_states import DeployStates
from keyboards.menus import deploy_type_keyboard
from services.openrouter import OpenRouterError, generate_text

router = Router()

DEPLOY_SYSTEM = (
    "Ты — опытный DevOps-инженер и ментор для начинающих разработчиков. "
    "Объясняй просто, без жаргона. Давай конкретные шаги (3–5 пунктов). "
    "Рекомендуй бесплатные или дешёвые решения (Railway, Render, Vercel, Fly.io, Netlify). "
    "Отвечай на русском языке."
)

DEPLOY_PROMPT = """Тип проекта: {project_type}

Код/описание проекта:
{code_input}

Задача: проанализируй проект и дай рекомендацию по деплою. Ответ структурируй так:

**🎯 Рекомендую:** [название платформы]
**Почему:** [1–2 предложения с конкретной причиной]

**📋 Шаги для деплоя:**
1. [конкретный шаг]
2. [конкретный шаг]
3. [конкретный шаг]
4. [если нужно]

**💰 Стоимость:** [бесплатно/примерная цена]

**⚠️ Важно:** [главный нюанс или возможная проблема]"""

TYPE_LABELS = {
    "telegram": "Telegram-бот",
    "website": "Веб-сайт",
    "api": "API-сервис",
}


@router.message(F.text == "🚀 Деплой")
async def deploy_enter(message: Message, state: FSMContext) -> None:
    await state.set_state(DeployStates.project_type)
    await message.answer(
        "🚀 <b>DeployAdvisor — твой личный DevOps</b>\n\n"
        "Что запускаем?",
        reply_markup=deploy_type_keyboard(),
    )


@router.callback_query(F.data.startswith("deploy_type:"))
async def deploy_choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    project_type = callback.data.split(":")[1]
    await state.update_data(project_type=TYPE_LABELS.get(project_type, project_type))
    await state.set_state(DeployStates.code_input)

    await callback.message.edit_text(
        f"✅ Тип: <b>{TYPE_LABELS.get(project_type, project_type)}</b>\n\n"
        "📎 <b>Скинь основной файл кода или опиши проект:</b>\n\n"
        "• Вставь код главного файла (bot.py / app.py / index.js)\n"
        "• Или опиши: стек, зависимости, что делает приложение\n"
        "• Или дай ссылку на GitHub-репозиторий\n\n"
        "<i>Чем больше деталей — тем точнее рекомендация.</i>\n\n"
        "Для отмены — /cancel"
    )
    await callback.answer()


@router.message(DeployStates.code_input)
async def deploy_analyze(message: Message, state: FSMContext) -> None:
    if not message.text and not message.document:
        await message.answer("Пожалуйста, вставь код или описание текстом. Для отмены — /cancel.")
        return

    # Обработка файла
    if message.document:
        if message.document.file_size and message.document.file_size > 5 * 1024 * 1024:
            await message.answer(
                "❗ Слишком большой файл. Отправь код текстом или ссылкой на GitHub."
            )
            return
        await message.answer(
            "📎 Файл получен! Но пока я работаю только с текстом — "
            "скопируй содержимое файла и пришли как сообщение."
        )
        return

    code_input = message.text.strip()
    data = await state.get_data()
    project_type = data.get("project_type", "неизвестный тип")
    await state.clear()

    thinking_msg = await message.answer("🔍 <b>Анализирую проект...</b> Подбираю лучший вариант деплоя.")

    try:
        prompt = DEPLOY_PROMPT.format(project_type=project_type, code_input=code_input[:3000])
        answer = await generate_text(
            prompt=prompt,
            system_prompt=DEPLOY_SYSTEM,
            max_tokens=1000,
            temperature=0.5,
        )

        await thinking_msg.delete()
        await message.answer(
            f"🚀 <b>Рекомендация по деплою</b>\n\n{answer}\n\n"
            f"💬 <i>Есть вопросы? Напиши — отвечу!</i>",
        )
        logger.info(f"Деплой-рекомендация для user_id={message.from_user.id}, type={project_type}")

    except OpenRouterError as e:
        logger.error(f"Ошибка deploy advisor: {e}")
        await thinking_msg.edit_text(
            "❗ Сервис временно перегружен. Попробуй через минуту."
        )
