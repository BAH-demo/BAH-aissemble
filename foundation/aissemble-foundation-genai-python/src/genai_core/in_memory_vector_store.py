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
import logging
import math
import uuid

from .genai_config import GenaiConfig
from .vector_store import Document, SearchResult, VectorStoreClient

logger = logging.getLogger(__name__)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b) or len(a) == 0:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore(VectorStoreClient):
    """Simple in-memory vector store for development and testing.

    Stores documents in a dict keyed by collection name. Performs brute-force
    cosine similarity search. Not intended for production use with large datasets.
    """

    def __init__(self, config: GenaiConfig | None = None):
        super().__init__(config)
        self._collections: dict[str, dict[str, Document]] = {}

    def _resolve_collection(self, collection: str) -> str:
        return collection or self._config.vector_store_collection()

    async def add_documents(
        self, documents: list[Document], collection: str = ""
    ) -> list[str]:
        """Add documents to the in-memory store."""
        coll = self._resolve_collection(collection)
        if coll not in self._collections:
            self._collections[coll] = {}

        ids = []
        for doc in documents:
            doc_id = doc.doc_id or str(uuid.uuid4())
            stored = Document(
                content=doc.content,
                metadata=doc.metadata,
                doc_id=doc_id,
                embedding=doc.embedding,
            )
            self._collections[coll][doc_id] = stored
            ids.append(doc_id)

        logger.info("Added %d documents to collection '%s'", len(ids), coll)
        return ids

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 0,
        collection: str = "",
        filters: dict | None = None,
    ) -> list[SearchResult]:
        """Search for similar documents using cosine similarity."""
        coll = self._resolve_collection(collection)
        k = top_k or self._config.rag_top_k()
        threshold = self._config.rag_similarity_threshold()

        if coll not in self._collections:
            return []

        results = []
        for doc in self._collections[coll].values():
            if filters:
                if not all(doc.metadata.get(fk) == fv for fk, fv in filters.items()):
                    continue
            score = _cosine_similarity(query_embedding, doc.embedding)
            if score >= threshold:
                results.append(SearchResult(document=doc, score=score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:k]

    async def delete_documents(
        self, doc_ids: list[str], collection: str = ""
    ) -> int:
        """Delete documents from the in-memory store."""
        coll = self._resolve_collection(collection)
        if coll not in self._collections:
            return 0

        deleted = 0
        for doc_id in doc_ids:
            if doc_id in self._collections[coll]:
                del self._collections[coll][doc_id]
                deleted += 1

        logger.info("Deleted %d documents from collection '%s'", deleted, coll)
        return deleted
