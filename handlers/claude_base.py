from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from keyboards.menus import ask_llm_keyboard
from services import knowledge_base
from services.openrouter import OpenRouterError, generate_text

router = Router()

CLAUDE_LLM_SYSTEM = (
    "Ты — эксперт по Claude Code (инструмент командной строки от Anthropic для разработки с AI). "
    "Отвечай кратко и точно на русском языке. "
    "Если не знаешь ответа — честно скажи об этом."
)


class ClaudeBaseStates(StatesGroup):
    waiting_question = State()
    waiting_llm_question = State()


@router.message(F.text == "📚 База Claude")
async def claude_base_enter(message: Message, state: FSMContext) -> None:
    await state.set_state(ClaudeBaseStates.waiting_question)

    commands = knowledge_base.get_all_commands()
    cmd_list = " • ".join(f"<code>{c['name']}</code>" for c in commands)

    await message.answer(
        "📚 <b>База знаний Claude Code</b>\n\n"
        f"Доступные команды: {cmd_list}\n\n"
        "Задай вопрос текстом — например:\n"
        "• <i>что делает /compact?</i>\n"
        "• <i>как управлять контекстом?</i>\n"
        "• <i>что такое effort levels?</i>\n\n"
        "Для отмены — /cancel"
    )


@router.message(ClaudeBaseStates.waiting_question)
async def claude_base_search(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Задай вопрос текстом. Для отмены — /cancel.")
        return

    query = message.text.strip()
    result = knowledge_base.search(query)

    if result:
        await message.answer(result)
        logger.debug(f"KB hit для query='{query[:50]}'")
    else:
        await state.update_data(pending_question=query)
        await message.answer(
            "🔍 <b>Не нашёл в базе знаний.</b>\n\n"
            "Могу спросить у AI — это может занять несколько секунд.",
            reply_markup=ask_llm_keyboard(),
        )


@router.callback_query(F.data == "claude_ask_llm")
async def claude_ask_llm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    question = data.get("pending_question", "")

    if not question:
        await callback.answer("Вопрос не найден. Задай снова.", show_alert=True)
        return

    await callback.message.edit_text("🤖 <b>Спрашиваю у AI...</b>")

    try:
        answer = await generate_text(
            prompt=f"Вопрос о Claude Code: {question}",
            system_prompt=CLAUDE_LLM_SYSTEM,
            max_tokens=600,
            temperature=0.5,
        )
        await callback.message.edit_text(
            f"🤖 <b>Ответ AI:</b>\n\n{answer}\n\n"
            f"<i>Этот ответ генерирует LLM — может быть неточным.</i>"
        )
        logger.info(f"LLM fallback для query='{question[:50]}'")

    except OpenRouterError as e:
        logger.error(f"Ошибка LLM fallback: {e}")
        await callback.message.edit_text(
            "❗ Сервис временно недоступен. Попробуй через минуту."
        )

    await callback.answer()


@router.message(Command("reload_kb"))
async def reload_kb(message: Message) -> None:
    knowledge_base.reload()
    await message.answer("✅ База знаний Claude перезагружена.")
