import asyncio
import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# Установка тестовых переменных окружения до импорта config
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "0:test_token")
os.environ.setdefault("OPENROUTER_API_KEY_TEXT", "test_key_text")
os.environ.setdefault("OPENROUTER_API_KEY_IMAGE", "test_key_image")
os.environ.setdefault("WEBHOOK_BASE_URL", "")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def tmp_db(tmp_path):
    db_file = tmp_path / "test.db"
    with patch("services.database.DB_PATH", db_file):
        from services.database import init_db
        await init_db()
        yield db_file


@pytest.fixture
def mock_generate_text():
    with patch("services.openrouter.generate_text", new_callable=AsyncMock) as mock:
        mock.return_value = "# Техническое задание: Тест\n## 1. Контекст\nТестовый контекст."
        yield mock


@pytest.fixture
def mock_generate_image():
    with patch("services.openrouter.generate_image", new_callable=AsyncMock) as mock:
        mock.return_value = b"fake_image_bytes"
        yield mock
