from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_generate_text_success(mock_generate_text):
    from services.openrouter import generate_text
    result = await generate_text("Тестовый промпт")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_text_parses_response():
    mock_response_data = {
        "choices": [{"message": {"content": "  Ответ от LLM  "}}],
        "usage": {"total_tokens": 100},
    }

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=mock_response_data)
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_resp)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession", return_value=mock_session):
        from services import openrouter
        result = await openrouter.generate_text("test prompt")
        assert result == "Ответ от LLM"


@pytest.mark.asyncio
async def test_generate_image_success(mock_generate_image):
    from services.openrouter import generate_image
    result = await generate_image("тестовый промпт для изображения")
    assert isinstance(result, bytes)
    assert len(result) > 0
