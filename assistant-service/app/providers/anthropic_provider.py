"""
Anthropic (Claude) provider implementation.
"""

import asyncio
import logging
from collections.abc import AsyncIterator

from anthropic import Anthropic, AsyncAnthropic

from ..config import settings
from .base import BaseProvider, ChatMessage, ProviderConfig

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider"""

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-sonnet-4-20250514"

    def _get_client(self):
        """Get Anthropic client"""
        api_key = self.config.api_key or settings.anthropic_api_key
        base_url = self.config.base_url or settings.anthropic_base_url

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        return AsyncAnthropic(**kwargs)

    def _get_sync_client(self):
        """Get sync Anthropic client for operations that work better synchronously"""
        api_key = self.config.api_key or settings.anthropic_api_key
        base_url = self.config.base_url or settings.anthropic_base_url

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url

        return Anthropic(**kwargs)

    async def is_available(self) -> bool:
        """Check if Anthropic is configured"""
        api_key = self.config.api_key or settings.anthropic_api_key
        return bool(api_key)

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion from Anthropic"""
        client = self._get_client()
        model = self.config.model or self.default_model

        # Build messages list (Anthropic uses separate system parameter)
        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        try:
            async with client.messages.stream(
                model=model,
                messages=api_messages,
                system=system_prompt or "",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic stream error: {e}")
            raise

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Non-streaming chat completion"""
        client = self._get_client()
        model = self.config.model or self.default_model

        api_messages = []
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        response = await client.messages.create(
            model=model,
            messages=api_messages,
            system=system_prompt or "",
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )

        # Extract text from content blocks
        return "".join(block.text for block in response.content if hasattr(block, "text"))

    def _fetch_models_sync(self) -> list[str]:
        """Synchronously fetch all models from Anthropic API with pagination."""
        client = self._get_sync_client()
        all_models = []
        after_id = None

        while True:
            page = (
                client.models.list(limit=100, after_id=after_id)
                if after_id
                else client.models.list(limit=100)
            )

            for model in page.data:
                logger.debug(f"Found Anthropic model: {model.id}")
                all_models.append(model.id)

            if not page.has_more:
                break
            after_id = page.last_id

        return all_models

    @staticmethod
    def _get_model_version_priority(model_name: str) -> int:
        """Get version priority for model sorting (lower = newer/better)."""
        if "sonnet-4" in model_name or "claude-4" in model_name:
            return 0
        if "3-7" in model_name or "3.7" in model_name:
            return 1
        if "3-5" in model_name or "3.5" in model_name:
            return 2
        if "opus" in model_name:
            return 3
        if "3" in model_name:
            return 4
        return 10

    @staticmethod
    def _get_model_type_priority(model_name: str) -> int:
        """Get model type priority for sorting (lower = preferred)."""
        if "sonnet" in model_name:
            return 0
        if "haiku" in model_name:
            return 1
        if "opus" in model_name:
            return 2
        return 5

    @staticmethod
    def _get_model_date_suffix(model_name: str) -> int:
        """Extract date suffix from model name for sorting (higher = newer)."""
        for part in reversed(model_name.split("-")):
            if part.isdigit() and len(part) == 8:
                return int(part)
        return 0

    def _model_sort_key(self, model_name: str) -> tuple[int, int, int, str]:
        """Generate sort key for model ordering (newest/best first)."""
        return (
            self._get_model_version_priority(model_name),
            self._get_model_type_priority(model_name),
            -self._get_model_date_suffix(model_name),
            model_name,
        )

    async def list_models(self) -> list[str]:
        """List available Anthropic models using the Models API"""
        loop = asyncio.get_event_loop()
        all_models = await loop.run_in_executor(None, self._fetch_models_sync)

        logger.info(f"Retrieved {len(all_models)} models from Anthropic API")

        if not all_models:
            raise RuntimeError("Anthropic API returned no models")

        all_models.sort(key=self._model_sort_key)
        return all_models
