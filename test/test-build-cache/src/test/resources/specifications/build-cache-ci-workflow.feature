@build-cache
Feature: CI/CD Build Cache Workflow Validation

  As a CI/CD engineer, I want to validate that the GitHub Actions workflow
  properly configures S3-backed caching for Maven builds.

  Scenario: CI workflow uses S3-backed cache for Maven repository
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 repository cache should use S3-backed storage
    And the m2 repository cache path should be "~/.m2/repository"

  Scenario: CI workflow uses S3-backed cache for Maven build cache
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 build cache should use S3-backed storage
    And the m2 build cache path should be "~/.m2/build-cache"

  Scenario: CI cache uses hash-based keys for repository cache
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 repository cache key should include a pom.xml hash

  Scenario: CI cache uses hash-based keys for build cache
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 build cache key should include source file hashes

  Scenario: CI cache has restore-keys fallback for repository cache
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 repository cache should have restore-keys fallback

  Scenario: CI cache has restore-keys fallback for build cache
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the m2 build cache should have restore-keys fallback

  Scenario: CI cache is skipped for scheduled builds
    Given the CI workflow configuration file exists
    When I read the CI workflow cache steps
    Then the cache restore steps should be skipped for scheduled builds

  Scenario: CI build uses parallel execution
    Given the CI workflow configuration file exists
    When I read the CI build step
    Then the build should use parallel execution with "-T8"
