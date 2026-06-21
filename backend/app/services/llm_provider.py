from __future__ import annotations

from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import logger


class LLMProvider:
    def __init__(self):
        if settings.LLM_PROVIDER == "ollama":
            self.client = AsyncOpenAI(
                api_key="ollama",
                base_url=settings.LLM_BASE_URL,
            )
        elif settings.LLM_PROVIDER == "openrouter":
            self.client = AsyncOpenAI(
                api_key=settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY,
                base_url="https://openrouter.ai/api/v1",
            )
        else:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.LLM_MODEL
        logger.info(f"Initialized LLM provider: {settings.LLM_PROVIDER} / {self.model}")

    async def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2000
    ) -> str:
        """Generate a response from the LLM."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    async def generate_stream(
        self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 2000
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from the LLM."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            raise


llm = LLMProvider()
