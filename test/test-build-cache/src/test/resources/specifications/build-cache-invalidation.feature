@build-cache
Feature: Build Cache Invalidation

  As a developer, I want the build cache to properly invalidate
  when source files change so that I always get fresh builds when needed.

  Scenario: Cache key changes when a Java source file is modified
    Given a set of source files for cache key computation
    When I modify a Java source file
    Then the computed cache key should differ from the original

  Scenario: Cache key changes when pom.xml is modified
    Given a set of source files for cache key computation
    When I modify the pom.xml file
    Then the computed cache key should differ from the original

  Scenario: Cache key remains stable when non-tracked files change
    Given a set of source files for cache key computation
    When I modify a non-tracked file like "README.md"
    Then the computed cache key should match the original

  Scenario: Cache key changes when a Python source file is modified
    Given a set of source files for cache key computation
    When I modify a Python source file
    Then the computed cache key should differ from the original

  Scenario: Cache key changes when a Dockerfile is modified
    Given a set of source files for cache key computation
    When I modify a Dockerfile
    Then the computed cache key should differ from the original

  Scenario: Poetry lock file changes do not invalidate cache
    Given a set of source files for cache key computation
    When I modify the "poetry.lock" file
    Then the computed cache key should match the original
