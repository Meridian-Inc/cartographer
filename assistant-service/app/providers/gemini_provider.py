"""
Google Gemini provider implementation.
"""

import logging
from collections.abc import AsyncIterator

import google.generativeai as genai

from ..config import settings
from .base import BaseProvider, ChatMessage, ProviderConfig

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    """Google Gemini API provider"""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return "gemini-2.5-flash"

    def _configure_genai(self):
        """Configure Google Generative AI"""
        api_key = self.config.api_key or settings.effective_google_api_key
        genai.configure(api_key=api_key)
        return genai

    async def is_available(self) -> bool:
        """Check if Gemini is configured"""
        api_key = self.config.api_key or settings.effective_google_api_key
        return bool(api_key)

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat completion from Gemini"""
        genai = self._configure_genai()
        model_name = self.config.model or self.default_model

        # Create model with system instruction
        generation_config = genai.types.GenerationConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
        )

        model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )

        # Convert messages to Gemini format
        # Gemini uses 'user' and 'model' roles
        history = []
        for msg in messages[:-1]:  # All but last message
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})

        # Start chat with history
        chat = model.start_chat(history=history)

        # Get last user message
        last_message = messages[-1].content if messages else ""

        try:
            response = await chat.send_message_async(last_message, stream=True)

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini stream error: {e}")
            raise

    async def chat(
        self,
        messages: list[ChatMessage],
        system_prompt: str | None = None,
    ) -> str:
        """Non-streaming chat completion"""
        genai = self._configure_genai()
        model_name = self.config.model or self.default_model

        generation_config = genai.types.GenerationConfig(
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_tokens,
        )

        model = genai.GenerativeModel(
            model_name,
            generation_config=generation_config,
            system_instruction=system_prompt,
        )

        # Convert messages
        history = []
        for msg in messages[:-1]:
            role = "model" if msg.role == "assistant" else "user"
            history.append({"role": role, "parts": [msg.content]})

        chat = model.start_chat(history=history)
        last_message = messages[-1].content if messages else ""

        response = await chat.send_message_async(last_message)
        return response.text

    def _is_chat_capable_model(self, model) -> bool:
        """Check if a model supports chat/generateContent."""
        supported_methods = getattr(model, "supported_generation_methods", [])
        return (
            "generateContent" in supported_methods or "streamGenerateContent" in supported_methods
        )

    def _is_valid_gemini_model(self, model_id: str) -> bool:
        """Check if a model ID is a valid Gemini chat model."""
        model_lower = model_id.lower()
        excluded = ["embedding", "aqa"]
        return "gemini" in model_lower and not any(x in model_lower for x in excluded)

    @staticmethod
    def _get_model_version_priority(model_name: str) -> int:
        """Get version priority for model sorting (lower = newer)."""
        if "2.0" in model_name or "2-0" in model_name:
            return 0
        if "1.5" in model_name or "1-5" in model_name:
            return 1
        return 2

    @staticmethod
    def _get_model_type_priority(model_name: str) -> int:
        """Get model type priority for sorting (lower = preferred)."""
        model_lower = model_name.lower()
        if "pro" in model_lower:
            return 0
        if "flash-8b" in model_lower:
            return 2
        if "flash" in model_lower:
            return 1
        return 3

    def _model_sort_key(self, model_name: str) -> tuple[int, int, str]:
        """Generate sort key for model ordering (newest/best first)."""
        return (
            self._get_model_version_priority(model_name),
            self._get_model_type_priority(model_name),
            model_name,
        )

    async def list_models(self) -> list[str]:
        """List available Gemini models from the API"""
        genai = self._configure_genai()

        chat_models = []
        for model in genai.list_models():
            model_id = model.name.removeprefix("models/")

            if self._is_chat_capable_model(model) and self._is_valid_gemini_model(model_id):
                chat_models.append(model_id)
                logger.debug(f"Found Gemini model: {model_id}")

        logger.info(f"Retrieved {len(chat_models)} models from Gemini API")

        if not chat_models:
            raise RuntimeError("Gemini API returned no models")

        chat_models.sort(key=self._model_sort_key)

        # Remove duplicates while preserving order
        seen = set()
        return [m for m in chat_models if not (m in seen or seen.add(m))]
