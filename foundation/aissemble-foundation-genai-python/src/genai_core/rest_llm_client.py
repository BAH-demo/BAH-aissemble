###
# #%L
# aiSSEMBLE Foundation::GenAI (Python)
# %%
# Copyright (C) 2021 Booz Allen
# %%
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# #L%
###
from __future__ import annotations

import logging
import os
from typing import Dict, List

import aiohttp

from .genai_config import GenaiConfig
from .llm_client import LlmClient
from .llm_message import LlmMessage, MessageRole
from .llm_response import LlmResponse, TokenUsage

logger = logging.getLogger(__name__)


class RestLlmClient(LlmClient):
    """LLM client that communicates with OpenAI-compatible REST APIs.

    Supports OpenAI, Azure OpenAI, vLLM, Ollama, and any provider
    exposing an OpenAI-compatible chat completions endpoint.
    """

    def __init__(self, config: GenaiConfig | None = None):  # noqa: FA100
        super().__init__(config)

    def _get_api_key(self) -> str:
        """Retrieve the API key from the configured environment variable."""
        env_var = self._config.llm_api_key_env_var()
        api_key = os.environ.get(env_var, "")
        if not api_key:
            logger.warning("LLM API key not found in environment variable '%s'", env_var)
        return api_key

    def _build_headers(self) -> Dict:
        """Build HTTP headers for the LLM API request."""
        headers = {
            "Content-Type": "application/json",
        }
        api_key = self._get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    def _build_chat_payload(
        self, messages: List[LlmMessage], **kwargs
    ) -> Dict:
        """Build the JSON payload for a chat completions request."""
        payload = {
            "model": kwargs.get("model", self._config.llm_model()),
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", self._config.llm_temperature()),
            "max_tokens": kwargs.get("max_tokens", self._config.llm_max_tokens()),
        }
        return payload

    async def generate(self, prompt: str, **kwargs) -> LlmResponse:
        """Generate a completion from a single prompt via the chat completions API."""
        messages = [LlmMessage(role=MessageRole.USER, content=prompt)]
        return await self.chat(messages, **kwargs)

    async def chat(self, messages: List[LlmMessage], **kwargs) -> LlmResponse:
        """Generate a completion from a multi-turn conversation."""
        url = f"{self._config.llm_api_base_url()}/chat/completions"
        headers = self._build_headers()
        payload = self._build_chat_payload(messages, **kwargs)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        choice = data["choices"][0]
        usage_data = data.get("usage", {})

        return LlmResponse(
            content=choice["message"]["content"],
            model=data.get("model", ""),
            usage=TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
            finish_reason=choice.get("finish_reason", ""),
        )
