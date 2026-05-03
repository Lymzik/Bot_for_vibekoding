from services.openrouter import generate_text

ENHANCER_SYSTEM = (
    "Ты — профессиональный prompt-инженер для text-to-image моделей (Flux, DALL-E, Midjourney). "
    "Твоя задача: взять короткое описание пользователя и расширить его до профессионального промпта. "
    "Выведи ТОЛЬКО промпт на английском языке, без объяснений и кавычек."
)

ENHANCER_PROMPT = (
    "Улучши следующее описание изображения до профессионального промпта для нейросети:\n\n"
    "Описание: {user_prompt}\n\n"
    "Добавь: стиль (photorealistic/vector/3D/flat design), освещение, детализацию, "
    "технические параметры (masterpiece, 8k, sharp focus, product shot, clean background и т.д.). "
    "Сделай промпт максимально конкретным и визуально богатым."
)


async def enhance_prompt(user_prompt: str) -> str:
    enhanced = await generate_text(
        prompt=ENHANCER_PROMPT.format(user_prompt=user_prompt),
        system_prompt=ENHANCER_SYSTEM,
        max_tokens=300,
        temperature=0.8,
    )
    return enhanced
