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

from pydantic import BaseModel, Field

from .document_chunker import DocumentChunker
from .embedding_client import EmbeddingClient
from .genai_config import GenaiConfig
from .llm_client import LlmClient
from .llm_message import LlmMessage, MessageRole
from .llm_response import LlmResponse
from .vector_store import Document, SearchResult, VectorStoreClient

logger = logging.getLogger(__name__)

DEFAULT_RAG_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer the user's question based on the "
    "provided context. If the context does not contain enough information to "
    "answer the question, say so clearly.\n\n"
    "Context:\n${context}"
)


class RagResponse(BaseModel):
    """Response from a RAG pipeline query."""

    answer: str
    source_documents: list[SearchResult] = Field(default_factory=list)
    llm_response: LlmResponse | None = None


class RagPipeline:
    """Retrieval-Augmented Generation pipeline.

    Orchestrates the full RAG workflow: embed the query, retrieve relevant
    documents from a vector store, construct a context-augmented prompt,
    and generate a response via an LLM.
    """

    def __init__(
        self,
        llm_client: LlmClient,
        embedding_client: EmbeddingClient,
        vector_store: VectorStoreClient,
        config: GenaiConfig | None = None,
        system_prompt: str = DEFAULT_RAG_SYSTEM_PROMPT,
    ):
        self._llm_client = llm_client
        self._embedding_client = embedding_client
        self._vector_store = vector_store
        self._config = config or GenaiConfig()
        self._chunker = DocumentChunker(self._config)
        self._system_prompt = system_prompt

    async def ingest(
        self, documents: list[Document], collection: str = ""
    ) -> list[str]:
        """Ingest documents into the vector store.

        Documents are chunked, embedded, and stored in the configured
        vector store collection.

        Args:
            documents: Source documents to ingest.
            collection: Target collection. Uses default from config if empty.

        Returns:
            List of stored document/chunk IDs.
        """
        chunks = self._chunker.chunk_many(documents)
        logger.info("Chunked %d documents into %d chunks", len(documents), len(chunks))

        texts = [chunk.content for chunk in chunks]
        if not texts:
            return []

        embeddings = await self._embedding_client.embed_batch(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        ids = await self._vector_store.add_documents(chunks, collection)
        logger.info("Ingested %d chunks into vector store", len(ids))
        return ids

    async def query(
        self,
        question: str,
        collection: str = "",
        top_k: int = 0,
        filters: dict | None = None,
        **llm_kwargs,
    ) -> RagResponse:
        """Run a RAG query: retrieve context, then generate an answer.

        Args:
            question: The user's question.
            collection: Vector store collection to search.
            top_k: Number of context documents to retrieve.
            filters: Optional metadata filters for retrieval.
            **llm_kwargs: Additional parameters passed to the LLM.

        Returns:
            RagResponse with the generated answer and source documents.
        """
        query_embedding = await self._embedding_client.embed(question)

        results = await self._vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k or self._config.rag_top_k(),
            collection=collection,
            filters=filters,
        )

        context = self._build_context(results)
        messages = self._build_messages(question, context)

        llm_response = await self._llm_client.chat(messages, **llm_kwargs)

        return RagResponse(
            answer=llm_response.content,
            source_documents=results,
            llm_response=llm_response,
        )

    def _build_context(self, results: list[SearchResult]) -> str:
        """Build a context string from search results."""
        if not results:
            return "No relevant context found."

        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.document.content}")
        return "\n\n".join(context_parts)

    def _build_messages(
        self, question: str, context: str
    ) -> list[LlmMessage]:
        """Build the chat messages for the LLM."""
        system_content = self._system_prompt.replace("${context}", context)
        return [
            LlmMessage(role=MessageRole.SYSTEM, content=system_content),
            LlmMessage(role=MessageRole.USER, content=question),
        ]
