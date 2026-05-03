
import pytest


@pytest.fixture(autouse=True)
def load_kb():
    from services import knowledge_base
    knowledge_base.load()


def test_search_compact_command():
    from services import knowledge_base
    result = knowledge_base.search("что делает /compact")
    assert result is not None
    assert "/compact" in result


def test_search_by_alias():
    from services import knowledge_base
    result = knowledge_base.search("сжать контекст")
    assert result is not None


def test_search_limits():
    from services import knowledge_base
    result = knowledge_base.search("сколько токенов в контексте")
    assert result is not None
    assert "200" in result


def test_search_effort_levels():
    from services import knowledge_base
    result = knowledge_base.search("что такое effort levels")
    assert result is not None
    assert "low" in result.lower() or "high" in result.lower()


def test_search_unknown_returns_none():
    from services import knowledge_base
    result = knowledge_base.search("абракадабра никому неизвестная ерунда zzz")
    assert result is None


def test_get_all_commands_not_empty():
    from services import knowledge_base
    commands = knowledge_base.get_all_commands()
    assert len(commands) >= 5


def test_reload():
    from services import knowledge_base
    knowledge_base.reload()
    commands = knowledge_base.get_all_commands()
    assert len(commands) >= 5
