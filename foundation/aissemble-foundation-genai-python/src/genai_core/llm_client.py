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

import abc
import logging
from typing import List

from .genai_config import GenaiConfig
from .llm_message import LlmMessage
from .llm_response import LlmResponse

logger = logging.getLogger(__name__)


class LlmClient(metaclass=abc.ABCMeta):
    """Abstract interface for interacting with language models.

    Implementations should provide connectivity to specific LLM providers
    (e.g., OpenAI, Azure OpenAI, local models via vLLM/Ollama).
    """

    _config: GenaiConfig

    def __init__(self, config: GenaiConfig | None = None):  # noqa: FA100
        self._config = config or GenaiConfig()

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "generate")
            and callable(subclass.generate)
            and hasattr(subclass, "chat")
            and callable(subclass.chat)
        )

    @abc.abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LlmResponse:
        """Generate a completion from a single prompt string.

        Args:
            prompt: The input text prompt.
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.).

        Returns:
            LlmResponse with generated text and metadata.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def chat(self, messages: List[LlmMessage], **kwargs) -> LlmResponse:
        """Generate a completion from a multi-turn conversation.

        Args:
            messages: Ordered list of conversation messages.
            **kwargs: Provider-specific parameters.

        Returns:
            LlmResponse with the assistant's reply and metadata.
        """
        raise NotImplementedError
