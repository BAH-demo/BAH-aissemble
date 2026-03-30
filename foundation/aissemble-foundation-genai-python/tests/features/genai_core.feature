Feature: GenAI Core Foundation
  As an aiSSEMBLE developer
  I want foundational GenAI abstractions
  So that I can build LLM-powered pipelines

  Scenario: Prompt template rendering
    Given a prompt template with variables
    When I render the template with values
    Then the rendered prompt contains the substituted values

  Scenario: Document chunking
    Given a long document
    When I chunk the document
    Then the document is split into overlapping chunks

  Scenario: In-memory vector store operations
    Given an in-memory vector store with documents
    When I search with a query embedding
    Then I receive relevant documents sorted by similarity

  Scenario: Prompt manager registration and retrieval
    Given a prompt manager with registered templates
    When I retrieve a template by name
    Then the correct template is returned
