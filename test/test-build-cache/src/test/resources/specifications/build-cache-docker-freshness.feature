@build-cache
Feature: Docker Image Freshness with Build Cache

  As a developer, I want the build cache to prevent stale Docker images
  by limiting the number of cached builds to 1.

  Scenario: Only one build is cached to prevent stale Docker images
    Given the Maven build cache configuration file exists
    When I read the local cache settings
    Then only 1 build should be cached

  Scenario: Cache comment documents the Docker image freshness rationale
    Given the Maven build cache configuration file exists
    When I read the raw configuration content
    Then the configuration should contain a comment about stale docker images

  Scenario: Archetype template inherits the same cache limit
    Given the archetype Maven build cache configuration file exists
    When I read the archetype cache configuration
    Then the archetype maximum builds cached should be 1
