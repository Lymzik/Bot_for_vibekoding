from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.menus import main_menu
from services.database import upsert_user

router = Router()

WELCOME_TEXT = (
    "⚡ <b>VibeMaster AI</b> — твой личный операционный центр вайб-кодера 🤖\n\n"
    "🌌 Превращаю мысли в ТЗ, ТЗ — в код и визуал.\n"
    "🧪 Обучаю работать с Claude Code как профи.\n\n"
    "<b>Выбери режим:</b>\n"
    "📚 <b>База Claude</b> — команды и фишки Claude Code\n"
    "📝 <b>Создать ТЗ</b> — пошаговый конструктор\n"
    "🎨 <b>Визуал</b> — генерация изображений с AI\n"
    "🚀 <b>Деплой</b> — куда и как задеплоить продукт"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нечего отменять. Ты в главном меню.", reply_markup=main_menu())
        return
    await state.clear()
    await message.answer(
        "❌ Операция отменена. Возвращаюсь в главное меню.",
        reply_markup=main_menu(),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    help_text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — главное меню\n"
        "/cancel — отмена текущей операции\n"
        "/history — последние 5 ТЗ\n"
        "/image — генерация изображения\n"
        "/reload_kb — перезагрузить базу знаний Claude\n"
        "/help — это сообщение"
    )
    await message.answer(help_text)
