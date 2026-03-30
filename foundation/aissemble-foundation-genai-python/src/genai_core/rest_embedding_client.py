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

from .embedding_client import EmbeddingClient
from .genai_config import GenaiConfig

logger = logging.getLogger(__name__)


class RestEmbeddingClient(EmbeddingClient):
    """Embedding client that communicates with OpenAI-compatible embeddings APIs.

    Supports OpenAI, Azure OpenAI, and any provider exposing an
    OpenAI-compatible embeddings endpoint.
    """

    def __init__(self, config: GenaiConfig | None = None):  # noqa: FA100
        super().__init__(config)

    def _get_api_key(self) -> str:
        """Retrieve the API key from the configured environment variable."""
        env_var = self._config.llm_api_key_env_var()
        return os.environ.get(env_var, "")

    def _build_headers(self) -> Dict:
        """Build HTTP headers for the embeddings API request."""
        headers = {"Content-Type": "application/json"}
        api_key = self._get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        return headers

    async def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple texts."""
        url = f"{self._config.llm_api_base_url()}/embeddings"
        headers = self._build_headers()
        payload = {
            "model": self._config.embedding_model(),
            "input": texts,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()

        # Sort by index to preserve input ordering
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
