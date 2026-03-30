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
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .genai_config import GenaiConfig

logger = logging.getLogger(__name__)


class Document(BaseModel):
    """A document with content and metadata for vector storage."""

    content: str
    metadata: dict = Field(default_factory=dict)
    doc_id: str = ""
    embedding: List[float] = Field(default_factory=list)


class SearchResult(BaseModel):
    """A single result from a vector similarity search."""

    document: Document
    score: float = 0.0


class VectorStoreClient(metaclass=abc.ABCMeta):
    """Abstract interface for vector database operations.

    Implementations should provide connectivity to specific vector stores
    (e.g., Qdrant, Milvus, pgvector, ChromaDB, in-memory).
    """

    _config: GenaiConfig

    def __init__(self, config: GenaiConfig | None = None):  # noqa: FA100
        self._config = config or GenaiConfig()

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "add_documents")
            and callable(subclass.add_documents)
            and hasattr(subclass, "search")
            and callable(subclass.search)
        )

    @abc.abstractmethod
    async def add_documents(
        self, documents: List[Document], collection: str = ""
    ) -> List[str]:
        """Add documents with their embeddings to the vector store.

        Args:
            documents: Documents to store, each with content and pre-computed embedding.
            collection: Target collection name. Uses default from config if empty.

        Returns:
            List of document IDs assigned by the store.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 0,
        collection: str = "",
        filters: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """Search for similar documents by embedding vector.

        Args:
            query_embedding: The query vector to search against.
            top_k: Number of results to return. Uses default from config if 0.
            collection: Collection to search. Uses default from config if empty.
            filters: Optional metadata filters to narrow results.

        Returns:
            List of SearchResult ordered by similarity (highest first).
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_documents(
        self, doc_ids: List[str], collection: str = ""
    ) -> int:
        """Delete documents from the vector store by ID.

        Args:
            doc_ids: List of document IDs to delete.
            collection: Collection to delete from. Uses default from config if empty.

        Returns:
            Number of documents deleted.
        """
        raise NotImplementedError
