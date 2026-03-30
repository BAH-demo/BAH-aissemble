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

logger = logging.getLogger(__name__)


class EmbeddingClient(metaclass=abc.ABCMeta):
    """Abstract interface for generating text embeddings.

    Implementations should provide connectivity to specific embedding providers
    (e.g., OpenAI embeddings API, sentence-transformers, local models).
    """

    _config: GenaiConfig

    def __init__(self, config: GenaiConfig | None = None):  # noqa: FA100
        self._config = config or GenaiConfig()

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "embed")
            and callable(subclass.embed)
            and hasattr(subclass, "embed_batch")
            and callable(subclass.embed_batch)
        )

    @abc.abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: The input text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors, one per input text.
        """
        raise NotImplementedError
