from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_upsert_and_get_user(tmp_db):
    from services.database import upsert_user
    with patch("services.database.DB_PATH", tmp_db):
        await upsert_user(123, "testuser")
        await upsert_user(123, "testuser_updated")  # повторный upsert


@pytest.mark.asyncio
async def test_save_and_get_tz(tmp_db):
    from services.database import get_user_tzs, save_tz, upsert_user
    with patch("services.database.DB_PATH", tmp_db):
        await upsert_user(456, "tzuser")
        tz_id = await save_tz(456, "# Тестовое ТЗ\n## 1. Контекст\nТест.")
        assert tz_id is not None

        tzs = await get_user_tzs(456)
        assert len(tzs) == 1
        assert "Тестовое ТЗ" in tzs[0]["content"]


@pytest.mark.asyncio
async def test_max_5_tzs_per_user(tmp_db):
    from services.database import get_user_tzs, save_tz, upsert_user
    with patch("services.database.DB_PATH", tmp_db):
        await upsert_user(789, "limituser")
        for i in range(7):
            await save_tz(789, f"# ТЗ #{i}")

        tzs = await get_user_tzs(789)
        assert len(tzs) <= 5, f"Должно быть не более 5 ТЗ, получено {len(tzs)}"


@pytest.mark.asyncio
async def test_log_generation(tmp_db):
    from services.database import log_generation, upsert_user
    with patch("services.database.DB_PATH", tmp_db):
        await upsert_user(111, "loguser")
        await log_generation(111, "tz", "claude-3.5-sonnet", True, tokens_used=500)
        await log_generation(111, "image", "flux-pro", False)
