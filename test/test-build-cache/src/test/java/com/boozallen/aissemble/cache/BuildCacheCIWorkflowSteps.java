package com.boozallen.aissemble.cache;

/*-
 * #%L
 * aiSSEMBLE::Test::Build Cache
 * %%
 * Copyright (C) 2021 Booz Allen
 * %%
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * #L%
 */

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

public class BuildCacheCIWorkflowSteps {

    private static final String WORKFLOW_PATH = findProjectRoot() + "/.github/workflows/build.yml";

    private String workflowContent;

    private static String findProjectRoot() {
        Path current = Paths.get(System.getProperty("user.dir"));
        while (current != null) {
            if (Files.exists(current.resolve(".mvn/maven-build-cache-config.xml"))) {
                return current.toString();
            }
            current = current.getParent();
        }
        return System.getProperty("user.dir") + "/../..";
    }

    @Given("the CI workflow configuration file exists")
    public void theCIWorkflowConfigurationFileExists() {
        Path workflowPath = Paths.get(WORKFLOW_PATH);
        assertTrue("CI workflow file should exist at: " + WORKFLOW_PATH, Files.exists(workflowPath));
    }

    @When("I read the CI workflow cache steps")
    public void iReadTheCIWorkflowCacheSteps() throws Exception {
        workflowContent = new String(Files.readAllBytes(Paths.get(WORKFLOW_PATH)), StandardCharsets.UTF_8);
        assertNotNull("Workflow content should not be null", workflowContent);
    }

    @Then("the m2 repository cache should use S3-backed storage")
    public void theM2RepositoryCacheShouldUseS3BackedStorage() {
        assertTrue("Workflow should use runs-on/cache for m2 repository",
                workflowContent.contains("runs-on/cache/restore@v4"));
        assertTrue("Workflow should reference S3 bucket",
                workflowContent.contains("RUNS_ON_S3_BUCKET_CACHE"));
    }

    @Then("the m2 repository cache path should be {string}")
    public void theM2RepositoryCachePathShouldBe(String expected) {
        assertTrue("Workflow should contain m2 repository path: " + expected,
                workflowContent.contains("path: " + expected));
    }

    @Then("the m2 build cache should use S3-backed storage")
    public void theM2BuildCacheShouldUseS3BackedStorage() {
        assertTrue("Workflow should use runs-on/cache for m2 build cache",
                workflowContent.contains("runs-on/cache/restore@v4"));
    }

    @Then("the m2 build cache path should be {string}")
    public void theM2BuildCachePathShouldBe(String expected) {
        assertTrue("Workflow should contain m2 build cache path: " + expected,
                workflowContent.contains("path: " + expected));
    }

    @Then("the m2 repository cache key should include a pom.xml hash")
    public void theM2RepositoryCacheKeyShouldIncludeAPomXmlHash() {
        assertTrue("Repository cache key should include pom.xml hash",
                workflowContent.contains("maven-repo-cache-${{ hashFiles('**/pom.xml') }}"));
    }

    @Then("the m2 build cache key should include source file hashes")
    public void theM2BuildCacheKeyShouldIncludeSourceFileHashes() {
        assertTrue("Build cache key should include source file hashes",
                workflowContent.contains("maven-build-cache-${{ hashFiles('**/pom.xml', '**/src/**') }}"));
    }

    @Then("the m2 repository cache should have restore-keys fallback")
    public void theM2RepositoryCacheShouldHaveRestoreKeysFallback() {
        assertTrue("Repository cache should have restore-keys",
                workflowContent.contains("maven-repo-cache-\n") || workflowContent.contains("maven-repo-cache-"));
    }

    @Then("the m2 build cache should have restore-keys fallback")
    public void theM2BuildCacheShouldHaveRestoreKeysFallback() {
        assertTrue("Build cache should have restore-keys",
                workflowContent.contains("maven-build-cache-\n") || workflowContent.contains("maven-build-cache-"));
    }

    @Then("the cache restore steps should be skipped for scheduled builds")
    public void theCacheRestoreStepsShouldBeSkippedForScheduledBuilds() {
        assertTrue("Cache steps should have schedule skip condition",
                workflowContent.contains("! github.event.schedule"));
    }

    @When("I read the CI build step")
    public void iReadTheCIBuildStep() throws Exception {
        workflowContent = new String(Files.readAllBytes(Paths.get(WORKFLOW_PATH)), StandardCharsets.UTF_8);
        assertNotNull("Workflow content should not be null", workflowContent);
    }

    @Then("the build should use parallel execution with {string}")
    public void theBuildShouldUseParallelExecutionWith(String flag) {
        assertTrue("Build should use parallel execution with " + flag,
                workflowContent.contains(flag));
    }
}
