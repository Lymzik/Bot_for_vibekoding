import json
from pathlib import Path

from loguru import logger

KB_PATH = Path(__file__).parent.parent / "data" / "claude_knowledge.json"

_kb_data: dict = {}


def load() -> None:
    global _kb_data
    try:
        with open(KB_PATH, encoding="utf-8") as f:
            _kb_data = json.load(f)
        logger.info("База знаний Claude загружена")
    except FileNotFoundError:
        logger.error(f"Файл базы знаний не найден: {KB_PATH}")
        _kb_data = {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга claude_knowledge.json: {e}")
        _kb_data = {}


def reload() -> None:
    load()


def search(query: str) -> str | None:
    if not _kb_data:
        return None

    query_lower = query.lower()

    # Поиск по командам
    for cmd in _kb_data.get("commands", []):
        name = cmd["name"].lower()
        aliases = [a.lower() for a in cmd.get("aliases", [])]
        if name in query_lower or any(alias in query_lower for alias in aliases):
            return _format_command(cmd)

    # Поиск по проблемам — слова запроса (>3 букв) ищем в тексте проблемы
    query_words = [w for w in query_lower.split() if len(w) > 3]
    for problem in _kb_data.get("common_problems", []):
        problem_text = problem["problem"].lower()
        if query_words and any(word in problem_text for word in query_words):
            return _format_problem(problem)

    # Поиск по лимитам
    if any(word in query_lower for word in ["лимит", "токен", "контекст", "200k", "limit", "token"]):
        return _format_limits()

    # Поиск по effort/уровням
    if any(word in query_lower for word in ["effort", "уровень", "быстрый", "медленный", "thinking"]):
        return _format_effort()

    # Поиск по советам
    tips = _kb_data.get("tips", [])
    for tip in tips:
        if any(word in tip.lower() for word in query_lower.split() if len(word) > 3):
            return f"💡 <b>Совет:</b>\n{tip}"

    return None


def get_all_commands() -> list[dict]:
    return _kb_data.get("commands", [])


def get_tips() -> list[str]:
    return _kb_data.get("tips", [])


def _format_command(cmd: dict) -> str:
    text = f"📌 <b>{cmd['name']}</b>\n\n"
    text += f"{cmd['description']}\n\n"
    if cmd.get("example"):
        text += f"<b>Пример использования:</b>\n<i>{cmd['example']}</i>\n\n"
    if cmd.get("when_to_use"):
        text += f"<b>Когда использовать:</b>\n{cmd['when_to_use']}"
    return text


def _format_problem(problem: dict) -> str:
    return (
        f"🔧 <b>Проблема:</b> {problem['problem']}\n\n"
        f"✅ <b>Решение:</b>\n{problem['solution']}"
    )


def _format_limits() -> str:
    limits = _kb_data.get("limits", {})
    return (
        f"📊 <b>Лимиты Claude Code</b>\n\n"
        f"• Контекст: <b>{limits.get('context_tokens', 200000):,}</b> токенов (~150 000 слов)\n"
        f"• Максимальный ответ: <b>{limits.get('output_tokens', 8192):,}</b> токенов\n"
        f"• Предупреждение при заполнении: <b>{limits.get('warning_at_percent', 80)}%</b>\n\n"
        f"{limits.get('description', '')}"
    )


def _format_effort() -> str:
    effort = _kb_data.get("effort_levels", {})
    levels = effort.get("levels", [])
    text = "⚡ <b>Уровни усилий (Effort) Claude Code</b>\n\n"
    for level in levels:
        text += f"{level['speed']} <b>{level['name'].upper()}</b> — {level['description']}\n\n"
    return text.strip()
