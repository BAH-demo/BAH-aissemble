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
import asyncio

from behave import given, when, then  # noqa: F811

from genai_core.document_chunker import DocumentChunker
from genai_core.genai_config import GenaiConfig
from genai_core.in_memory_vector_store import InMemoryVectorStore
from genai_core.prompt_manager import PromptManager, PromptTemplate
from genai_core.vector_store import Document


def run_async(coro):
    """Helper to run async functions in behave steps."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# -- Prompt template rendering --


@given("a prompt template with variables")
def step_given_prompt_template(context):
    context.template = PromptTemplate(
        name="test_prompt",
        template="Hello $name, you are a $role.",
        description="Test template",
    )


@when("I render the template with values")
def step_when_render_template(context):
    context.rendered = context.template.render(name="Alice", role="developer")


@then("the rendered prompt contains the substituted values")
def step_then_rendered_contains_values(context):
    assert "Alice" in context.rendered, f"Expected 'Alice' in '{context.rendered}'"
    assert "developer" in context.rendered, f"Expected 'developer' in '{context.rendered}'"
    assert "$name" not in context.rendered, "Variable $name was not substituted"


# -- Document chunking --


@given("a long document")
def step_given_long_document(context):
    context.document = Document(
        content="This is sentence one. " * 100,
        metadata={"source": "test"},
        doc_id="doc1",
    )


@when("I chunk the document")
def step_when_chunk_document(context):
    config = GenaiConfig()
    chunker = DocumentChunker(config)
    context.chunks = chunker.chunk(context.document)


@then("the document is split into overlapping chunks")
def step_then_document_split(context):
    assert len(context.chunks) > 1, f"Expected multiple chunks, got {len(context.chunks)}"
    for i, chunk in enumerate(context.chunks):
        assert chunk.content, f"Chunk {i} has empty content"
        assert chunk.metadata.get("chunk_index") == i, (
            f"Chunk {i} has wrong chunk_index: {chunk.metadata.get('chunk_index')}"
        )


# -- In-memory vector store --


@given("an in-memory vector store with documents")
def step_given_vector_store(context):
    context.store = InMemoryVectorStore()
    docs = [
        Document(
            content="Python is a programming language",
            embedding=[1.0, 0.0, 0.0],
            doc_id="d1",
        ),
        Document(
            content="Java is a programming language",
            embedding=[0.9, 0.1, 0.0],
            doc_id="d2",
        ),
        Document(
            content="Cooking recipes for dinner",
            embedding=[0.0, 0.0, 1.0],
            doc_id="d3",
        ),
    ]
    run_async(context.store.add_documents(docs))


@when("I search with a query embedding")
def step_when_search(context):
    query = [1.0, 0.0, 0.0]  # Most similar to "Python is a programming language"
    context.results = run_async(context.store.search(query, top_k=2))


@then("I receive relevant documents sorted by similarity")
def step_then_relevant_results(context):
    assert len(context.results) > 0, "Expected at least one result"
    assert context.results[0].document.doc_id == "d1", (
        f"Expected 'd1' as top result, got '{context.results[0].document.doc_id}'"
    )
    if len(context.results) > 1:
        assert context.results[0].score >= context.results[1].score, (
            "Results should be sorted by descending similarity"
        )


# -- Prompt manager --


@given("a prompt manager with registered templates")
def step_given_prompt_manager(context):
    context.manager = PromptManager()
    context.manager.register(
        PromptTemplate(
            name="greeting",
            template="Hello $name!",
            version="1.0",
        )
    )
    context.manager.register(
        PromptTemplate(
            name="farewell",
            template="Goodbye $name!",
            version="1.0",
        )
    )


@when("I retrieve a template by name")
def step_when_retrieve_template(context):
    context.retrieved = context.manager.get("greeting")


@then("the correct template is returned")
def step_then_correct_template(context):
    assert context.retrieved.name == "greeting", (
        f"Expected 'greeting', got '{context.retrieved.name}'"
    )
    rendered = context.retrieved.render(name="World")
    assert rendered == "Hello World!", f"Expected 'Hello World!', got '{rendered}'"
