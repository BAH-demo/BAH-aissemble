# aiSSEMBLE Foundation GenAI (Python)

Foundation library for building LLM/GenAI pipelines with aiSSEMBLE. Provides:

- **LLM Client Abstractions** - Pluggable interface for interacting with language models (OpenAI, Azure OpenAI, local models)
- **RAG Pipeline Support** - Base classes for retrieval-augmented generation pipelines
- **Vector Store Interfaces** - Abstract interface for vector database operations with built-in implementations
- **Prompt Management** - Template-based prompt construction with versioning support

## Usage

This library is intended to be used as a foundation dependency in aiSSEMBLE GenAI pipeline projects generated via MDA.

```python
from genai_core.llm_client import LlmClient
from genai_core.rag_pipeline import RagPipeline
from genai_core.vector_store import VectorStoreClient
from genai_core.prompt_manager import PromptManager
```
