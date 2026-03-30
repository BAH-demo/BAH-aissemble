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

from .genai_config import GenaiConfig
from .vector_store import Document

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits documents into smaller chunks for embedding and vector storage.

    Uses configurable chunk size and overlap from GenaiConfig. Splitting
    is performed at sentence boundaries when possible to preserve coherence.
    """

    def __init__(self, config: GenaiConfig | None = None):
        self._config = config or GenaiConfig()

    def chunk(self, document: Document) -> list[Document]:
        """Split a document into chunks.

        Args:
            document: The source document to split.

        Returns:
            List of Document chunks, each inheriting the source's metadata
            plus a 'chunk_index' field.
        """
        chunk_size = self._config.chunk_size()
        overlap = self._config.chunk_overlap()
        text = document.content

        if not text:
            return []

        if len(text) <= chunk_size:
            return [
                Document(
                    content=text,
                    metadata={**document.metadata, "chunk_index": 0},
                    doc_id=f"{document.doc_id}_chunk_0" if document.doc_id else "",
                )
            ]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                # Try to break at a sentence boundary
                boundary = text.rfind(". ", start, end)
                if boundary > start:
                    end = boundary + 2  # Include the period and space

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_metadata = {**document.metadata, "chunk_index": chunk_index}
                chunks.append(
                    Document(
                        content=chunk_text,
                        metadata=chunk_metadata,
                        doc_id=(
                            f"{document.doc_id}_chunk_{chunk_index}"
                            if document.doc_id
                            else ""
                        ),
                    )
                )
                chunk_index += 1

            start = end - overlap
            if start >= len(text):
                break

        logger.info(
            "Split document into %d chunks (size=%d, overlap=%d)",
            len(chunks),
            chunk_size,
            overlap,
        )
        return chunks

    def chunk_many(self, documents: list[Document]) -> list[Document]:
        """Split multiple documents into chunks.

        Args:
            documents: List of source documents.

        Returns:
            Flat list of all document chunks.
        """
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk(doc))
        return all_chunks
