import html as html_module

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from loguru import logger

from fsm.tz_states import TZStates
from keyboards.menus import tz_confirm_keyboard, tz_done_keyboard
from services import database
from services.openrouter import OpenRouterError, generate_text

router = Router()

STEPS = [
    ("goal", "🎯 <b>Шаг 1/5.</b> Опиши основную цель продукта (1–2 предложения).\n\n<i>Пример: Сделать Telegram-бота, который помогает вести личный бюджет.</i>"),
    ("audience", "👥 <b>Шаг 2/5.</b> Кто целевая аудитория?\n\n<i>Пример: Студенты и молодые специалисты 18–30 лет.</i>"),
    ("features", "⚙️ <b>Шаг 3/5.</b> Перечисли ключевые функции через запятую.\n\n<i>Пример: добавление трат, просмотр статистики, напоминания, экспорт в CSV.</i>"),
    ("constraints", "🔧 <b>Шаг 4/5.</b> Технические ограничения (стек, бюджет, API-ключи).\n\n<i>Это необязательно — напиши «нет» если ограничений нет.</i>"),
    ("result", "🏁 <b>Шаг 5/5.</b> Желаемый результат?\n\n<i>Пример: MVP за 2 дня, рабочий прототип для демо, готовый продукт.</i>"),
]

TZ_SYSTEM_PROMPT = (
    "Ты — опытный технический писатель. Составь структурированное, чёткое "
    "техническое задание на русском языке строго по данным пользователя. "
    "Выведи только Markdown, без вступлений и объяснений."
)

TZ_PROMPT_TEMPLATE = """Составь ТЗ по следующим данным:

Цель продукта: {goal}
Целевая аудитория: {audience}
Ключевые функции: {features}
Технические ограничения: {constraints}
Желаемый результат: {result}

Используй строго эту структуру:
# Техническое задание: {goal}

## 1. Контекст
(2–3 предложения о проблеме и решении)

## 2. Целевая аудитория
(описание пользователей)

## 3. Функциональные требования
(нумерованный список функций)

## 4. Технические ограничения
(список или «Ограничений нет»)

## 5. Критерии приёмки
(4–6 конкретных, проверяемых критериев — что должно работать, чтобы ТЗ считалось выполненным)"""


@router.message(F.text == "📝 Создать ТЗ")
async def start_tz(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TZStates.goal)
    await message.answer(STEPS[0][1])


@router.message(TZStates.goal)
async def step_goal(message: Message, state: FSMContext) -> None:
    await _handle_step(message, state, "goal", 0, TZStates.audience)


@router.message(TZStates.audience)
async def step_audience(message: Message, state: FSMContext) -> None:
    await _handle_step(message, state, "audience", 1, TZStates.features)


@router.message(TZStates.features)
async def step_features(message: Message, state: FSMContext) -> None:
    await _handle_step(message, state, "features", 2, TZStates.constraints)


@router.message(TZStates.constraints)
async def step_constraints(message: Message, state: FSMContext) -> None:
    await _handle_step(message, state, "constraints", 3, TZStates.result)


@router.message(TZStates.result)
async def step_result(message: Message, state: FSMContext) -> None:
    await state.update_data(result=message.text.strip())
    data = await state.get_data()
    await state.clear()

    thinking_msg = await message.answer("✍️ <b>Думаю...</b> Генерирую ТЗ, это займёт несколько секунд.")

    try:
        prompt = TZ_PROMPT_TEMPLATE.format(**data)
        tz_content = await generate_text(
            prompt=prompt,
            system_prompt=TZ_SYSTEM_PROMPT,
            max_tokens=2048,
            temperature=0.6,
        )

        await database.save_tz(message.from_user.id, tz_content)
        await database.log_generation(
            user_id=message.from_user.id,
            gen_type="tz",
            model_used="default_text",
            success=True,
        )

        await thinking_msg.delete()
        await message.answer(
            f"✅ <b>ТЗ готово!</b>\n\n<pre>{html_module.escape(tz_content)}</pre>",
            reply_markup=tz_done_keyboard(),
        )
        logger.info(f"ТЗ сгенерировано для user_id={message.from_user.id}")

    except OpenRouterError as e:
        await database.log_generation(
            user_id=message.from_user.id,
            gen_type="tz",
            model_used="default_text",
            success=False,
        )
        logger.error(f"Ошибка генерации ТЗ: {e}")
        await thinking_msg.edit_text(
            "❗ Сервис временно перегружен. Попробуй через минуту.\n"
            "Используй /start чтобы вернуться в меню."
        )


async def _handle_step(
    message: Message,
    state: FSMContext,
    field: str,
    step_index: int,
    next_state: type,
) -> None:
    if not message.text:
        await message.answer("Пожалуйста, отвечай текстом. Для отмены введи /cancel.")
        return

    await state.update_data(**{field: message.text.strip()})
    await state.set_state(next_state)

    next_step_index = step_index + 1
    next_text = STEPS[next_step_index][1]
    await message.answer(
        f"✅ Принято.\n\n{next_text}",
        reply_markup=tz_confirm_keyboard(step_index),
    )


@router.callback_query(F.data.startswith("tz_back:"))
async def tz_go_back(callback: CallbackQuery, state: FSMContext) -> None:
    step_index = int(callback.data.split(":")[1])
    state_map = [TZStates.goal, TZStates.audience, TZStates.features, TZStates.constraints, TZStates.result]
    await state.set_state(state_map[step_index])

    await callback.message.edit_text(
        f"↩️ Изменяем шаг {step_index + 1}.\n\n{STEPS[step_index][1]}"
    )
    await callback.answer()


@router.callback_query(F.data == "tz_new")
async def tz_start_new(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TZStates.goal)
    await callback.message.answer(STEPS[0][1])
    await callback.answer()


@router.callback_query(F.data == "tz_copy")
async def tz_copy_hint(callback: CallbackQuery) -> None:
    await callback.answer(
        "Зажми на тексте ТЗ → «Копировать текст» 📋",
        show_alert=True,
    )
