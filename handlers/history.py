import html as html_module

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards.menus import history_item_keyboard
from services.database import get_tz_by_id, get_user_tzs

router = Router()


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    tzs = await get_user_tzs(message.from_user.id, limit=5)

    if not tzs:
        await message.answer(
            "📜 <b>История ТЗ</b>\n\n"
            "Пока нет сохранённых ТЗ. Создай первое через кнопку «📝 Создать ТЗ»!"
        )
        return

    await message.answer(f"📜 <b>Твои последние ТЗ ({len(tzs)} шт.):</b>")

    for i, tz in enumerate(tzs, 1):
        preview = tz["content"][:120].replace("<", "&lt;").replace(">", "&gt;")
        if len(tz["content"]) > 120:
            preview += "..."

        created = tz["created_at"][:16] if tz["created_at"] else "—"

        await message.answer(
            f"<b>#{i}</b> — <i>{created}</i>\n{preview}",
            reply_markup=history_item_keyboard(tz["id"]),
        )


@router.callback_query(F.data.startswith("history_show:"))
async def history_show_full(callback: CallbackQuery) -> None:
    tz_id = int(callback.data.split(":")[1])
    tz = await get_tz_by_id(tz_id, callback.from_user.id)

    if not tz:
        await callback.answer("ТЗ не найдено.", show_alert=True)
        return

    created = tz["created_at"][:16] if tz["created_at"] else "—"
    content = tz["content"]

    # Telegram лимит — 4096 символов на сообщение
    safe = html_module.escape(content)
    if len(safe) > 3800:
        await callback.message.answer(
            f"📄 <b>ТЗ от {created}</b>\n\n<pre>{safe[:3800]}</pre>\n\n"
            f"<i>...текст обрезан. Полное ТЗ занимает {len(content)} символов.</i>"
        )
    else:
        await callback.message.answer(
            f"📄 <b>ТЗ от {created}</b>\n\n<pre>{safe}</pre>"
        )

    await callback.answer()
