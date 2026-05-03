import asyncio
import urllib.parse
from typing import Any

import aiohttp
from loguru import logger
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import settings

_RETRYABLE = (aiohttp.ClientError, asyncio.TimeoutError)

HEADERS_TEXT = {
    "Authorization": f"Bearer {settings.openrouter_api_key_text}",
    "HTTP-Referer": "https://vibemaster.ai",
    "X-Title": "VibeMaster AI",
    "Content-Type": "application/json",
}

HEADERS_IMAGE = {
    "Authorization": f"Bearer {settings.openrouter_api_key_image}",
    "HTTP-Referer": "https://vibemaster.ai",
    "X-Title": "VibeMaster AI",
    "Content-Type": "application/json",
}

FALLBACK_IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"


def _is_retryable_status(status: int) -> bool:
    return status in (429, 500, 502, 503, 504)


class OpenRouterError(Exception):
    pass


class OpenRouterRateLimitError(OpenRouterError):
    pass


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def generate_text(
    prompt: str,
    system_prompt: str = "",
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    model = model or settings.default_text_model
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{settings.openrouter_base_url}/chat/completions",
            json=payload,
            headers=HEADERS_TEXT,
        ) as resp:
            if resp.status == 429:
                logger.warning(f"OpenRouter rate limit (text). Model: {model}")
                await asyncio.sleep(3)
                raise aiohttp.ClientError("Rate limited")
            if _is_retryable_status(resp.status):
                raise aiohttp.ClientError(f"Server error {resp.status}")
            if resp.status != 200:
                body = await resp.text()
                raise OpenRouterError(f"HTTP {resp.status}: {body[:200]}")

            data = await resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens")
        logger.debug(f"generate_text: model={model}, tokens={tokens}")
        return content.strip()
    except (KeyError, IndexError) as e:
        raise OpenRouterError(f"Неожиданный формат ответа: {data}") from e


async def generate_image(prompt: str, model: str | None = None) -> bytes:
    model = model or settings.default_image_model
    try:
        return await _generate_image_request(prompt, model, HEADERS_IMAGE)
    except OpenRouterError as exc:
        if "402" in str(exc):
            logger.warning("OpenRouter: недостаточно кредитов. Переключаюсь на Pollinations.ai (бесплатно).")
            return await _generate_image_pollinations(prompt)
        logger.warning(f"Основная модель {model} упала: {exc}. Пробую fallback {FALLBACK_IMAGE_MODEL}")
        return await _generate_image_request(prompt, FALLBACK_IMAGE_MODEL, HEADERS_IMAGE)
    except Exception as exc:
        logger.warning(f"Основная модель {model} упала: {exc}. Пробую Pollinations.ai.")
        return await _generate_image_pollinations(prompt)


async def _generate_image_pollinations(prompt: str) -> bytes:
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&enhance=true"
    logger.debug(f"Pollinations.ai запрос: {prompt[:60]}...")
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise OpenRouterError(f"Pollinations.ai: HTTP {resp.status}")
            image_bytes = await resp.read()
    logger.debug(f"Pollinations.ai: получено {len(image_bytes)} байт")
    return image_bytes


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _generate_image_request(prompt: str, model: str, headers: dict | None = None) -> bytes:
    # OpenRouter генерирует изображения через /chat/completions, а не /images/generations
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    _headers = headers if headers is not None else HEADERS_IMAGE
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(
            f"{settings.openrouter_base_url}/chat/completions",
            json=payload,
            headers=_headers,
        ) as resp:
            if resp.status == 429:
                await asyncio.sleep(3)
                raise aiohttp.ClientError("Rate limited")
            if _is_retryable_status(resp.status):
                raise aiohttp.ClientError(f"Server error {resp.status}")
            if resp.status != 200:
                body = await resp.text()
                raise OpenRouterError(f"HTTP {resp.status}: {body[:200]}")

            data = await resp.json()

    # Ответ: изображение может быть в message.content или в нестандартном message.images
    message = data["choices"][0]["message"]
    image_url = _extract_image_url(message.get("content")) or _extract_image_url(message.get("images"))
    if not image_url:
        raise OpenRouterError(f"Изображение не найдено в ответе модели: {str(data)[:300]}")

    logger.debug(f"Скачиваю изображение: {image_url[:60]}...")

    # data:image/... — base64 прямо в URL
    if image_url.startswith("data:image/"):
        import base64
        header, b64data = image_url.split(",", 1)
        return base64.b64decode(b64data)

    dl_timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=dl_timeout) as session:
        async with session.get(image_url) as resp:
            if resp.status != 200:
                raise OpenRouterError(f"Не удалось скачать изображение: HTTP {resp.status}")
            return await resp.read()


def _extract_image_url(content: Any) -> str | None:
    """Извлекает URL или base64 изображения из content или images поля ответа."""
    if not content:
        return None
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                return part.get("image_url", {}).get("url")
    return None
