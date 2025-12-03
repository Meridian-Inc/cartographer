"""
Anthropic (Claude) provider implementation.
"""

import os
import logging
from typing import AsyncIterator, List, Optional

from .base import BaseProvider, ProviderConfig, ChatMessage

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude API provider"""
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"
    
    def _get_client(self):
        """Get Anthropic client"""
        from anthropic import AsyncAnthropic
        
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        base_url = self.config.base_url or os.environ.get("ANTHROPIC_BASE_URL")
        
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
            
        return AsyncAnthropic(**kwargs)
    
    async def is_available(self) -> bool:
        """Check if Anthropic is configured"""
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        return bool(api_key)
    
    async def stream_chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
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
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
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
        return "".join(
            block.text for block in response.content 
            if hasattr(block, 'text')
        )
    
    async def list_models(self) -> List[str]:
        """List available Anthropic models from the API"""
        try:
            client = self._get_client()
            # Anthropic has a models list endpoint
            models_response = await client.models.list(limit=100)
            
            chat_models = []
            for model in models_response.data:
                model_id = model.id
                # Include Claude models
                if model_id.startswith('claude'):
                    chat_models.append(model_id)
            
            # Sort with newest models first (by date suffix, descending)
            def sort_key(model_name):
                # Extract version info: claude-3-5-sonnet-20241022
                parts = model_name.split('-')
                # Priority: claude-3-5 > claude-3, sonnet > haiku > opus (for cost/performance balance)
                version_priority = 0
                if '3-5' in model_name or '3.5' in model_name:
                    version_priority = 0
                elif '3' in model_name:
                    version_priority = 1
                else:
                    version_priority = 2
                
                # Get date suffix if present
                date_suffix = ''
                for part in reversed(parts):
                    if part.isdigit() and len(part) == 8:
                        date_suffix = part
                        break
                
                return (version_priority, -int(date_suffix) if date_suffix else 0, model_name)
            
            chat_models.sort(key=sort_key)
            
            return chat_models if chat_models else [self.default_model]
            
        except Exception as e:
            logger.warning(f"Failed to list Anthropic models: {e}")
            # Fallback to known models
            return [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
