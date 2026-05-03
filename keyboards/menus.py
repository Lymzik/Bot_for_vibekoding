from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📚 База Claude"),
                KeyboardButton(text="📝 Создать ТЗ"),
            ],
            [
                KeyboardButton(text="🎨 Визуал"),
                KeyboardButton(text="🚀 Деплой"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


def tz_confirm_keyboard(step: int) -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text="↩️ Изменить предыдущий", callback_data=f"tz_back:{step}")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def tz_done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Скопировать", callback_data="tz_copy"),
                InlineKeyboardButton(text="🔄 Создать ещё", callback_data="tz_new"),
            ]
        ]
    )


def deploy_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Telegram-бот", callback_data="deploy_type:telegram")],
            [InlineKeyboardButton(text="🌐 Веб-сайт", callback_data="deploy_type:website")],
            [InlineKeyboardButton(text="⚙️ API-сервис", callback_data="deploy_type:api")],
        ]
    )


def ask_llm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Уточнить у AI", callback_data="claude_ask_llm")]
        ]
    )


def history_item_keyboard(tz_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Показать", callback_data=f"history_show:{tz_id}")]
        ]
    )
