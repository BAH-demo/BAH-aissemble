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
"""
Configurations for GenAI services, read from genai.properties via Krausening.
"""

from krausening.properties import PropertyManager


class GenaiConfig:
    """
    Configurations for GenAI LLM and RAG pipeline settings.
    Reads from genai.properties using Krausening for environment-specific overrides.
    """

    def __init__(self):
        property_manager = PropertyManager.get_instance()
        self.properties = property_manager.get_properties("genai.properties")

    def llm_provider(self) -> str:
        """Returns the configured LLM provider (e.g., 'openai', 'azure_openai', 'local')."""
        return self.properties.getProperty("llm_provider", "openai")

    def llm_model(self) -> str:
        """Returns the LLM model identifier."""
        return self.properties.getProperty("llm_model", "gpt-4")

    def llm_api_base_url(self) -> str:
        """Returns the base URL for the LLM API."""
        return self.properties.getProperty("llm_api_base_url", "https://api.openai.com/v1")

    def llm_api_key_env_var(self) -> str:
        """Returns the environment variable name holding the LLM API key."""
        return self.properties.getProperty("llm_api_key_env_var", "LLM_API_KEY")

    def llm_temperature(self) -> float:
        """Returns the temperature setting for LLM generation."""
        return float(self.properties.getProperty("llm_temperature", "0.7"))

    def llm_max_tokens(self) -> int:
        """Returns the maximum number of tokens for LLM generation."""
        return int(self.properties.getProperty("llm_max_tokens", "2048"))

    def vector_store_provider(self) -> str:
        """Returns the configured vector store provider."""
        return self.properties.getProperty("vector_store_provider", "in_memory")

    def vector_store_url(self) -> str:
        """Returns the vector store connection URL."""
        return self.properties.getProperty("vector_store_url", "http://localhost:6333")

    def vector_store_collection(self) -> str:
        """Returns the default vector store collection name."""
        return self.properties.getProperty("vector_store_collection", "default")

    def embedding_model(self) -> str:
        """Returns the embedding model identifier."""
        return self.properties.getProperty("embedding_model", "text-embedding-ada-002")

    def embedding_dimensions(self) -> int:
        """Returns the dimensionality of the embedding vectors."""
        return int(self.properties.getProperty("embedding_dimensions", "1536"))

    def rag_top_k(self) -> int:
        """Returns the number of top results to retrieve in RAG queries."""
        return int(self.properties.getProperty("rag_top_k", "5"))

    def rag_similarity_threshold(self) -> float:
        """Returns the minimum similarity threshold for RAG retrieval."""
        return float(self.properties.getProperty("rag_similarity_threshold", "0.7"))

    def chunk_size(self) -> int:
        """Returns the chunk size for document splitting."""
        return int(self.properties.getProperty("chunk_size", "1000"))

    def chunk_overlap(self) -> int:
        """Returns the overlap between document chunks."""
        return int(self.properties.getProperty("chunk_overlap", "200"))
