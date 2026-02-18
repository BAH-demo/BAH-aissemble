@build-cache
Feature: Build Cache Configuration Validation

  As a developer, I want to ensure the Maven build cache is properly configured
  so that builds are faster and cache behavior is predictable.

  Scenario: Build cache is enabled by default
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the build cache should be enabled

  Scenario: Build cache uses SHA-256 hashing
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the hash algorithm should be "SHA-256"

  Scenario: XML validation is enabled
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then XML validation should be enabled

  Scenario: Remote cache is disabled for local development
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the remote cache should be disabled

  Scenario: Maximum builds cached is set to 1 for Docker image freshness
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the maximum builds cached should be 1

  Scenario: Cache includes required source directories
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the cache input should include "src/"
    And the cache input should include "pom.xml"

  Scenario: Cache tracks all required file types
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the cache glob should include "*.java"
    And the cache glob should include "*.xml"
    And the cache glob should include "*.py"
    And the cache glob should include "Dockerfile"
    And the cache glob should include "*.feature"

  Scenario: Install and deploy goals always run
    Given the Maven build cache configuration file exists
    When I read the cache configuration
    Then the "maven-install-plugin" goal "install" should always run
    And the "maven-deploy-plugin" goal "deploy" should always run
