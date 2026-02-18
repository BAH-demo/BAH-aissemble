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

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import io.cucumber.java.After;
import io.cucumber.java.Before;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

public class BuildCacheInvalidationSteps {

    private Path tempDir;
    private String originalCacheKey;
    private String currentCacheKey;
    private Map<String, String> fileContents;

    private static final List<String> TRACKED_EXTENSIONS = Arrays.asList(
            ".java", ".json", ".groovy", ".yaml", ".svcd", ".proto",
            ".xml", ".vm", ".ini", ".jks", ".properties", ".sh", ".bat", ".py"
    );
    private static final List<String> TRACKED_FILENAMES = Arrays.asList("Dockerfile");
    private static final List<String> EXCLUDED_FILES = Arrays.asList("poetry.lock", "Chart.lock");

    @Before("@build-cache")
    public void setUp() throws IOException {
        tempDir = Files.createTempDirectory("build-cache-test");
        fileContents = new HashMap<>();
    }

    @After("@build-cache")
    public void tearDown() throws IOException {
        if (tempDir != null) {
            org.apache.commons.io.FileUtils.deleteDirectory(tempDir.toFile());
        }
    }

    @Given("a set of source files for cache key computation")
    public void aSetOfSourceFilesForCacheKeyComputation() throws IOException, NoSuchAlgorithmException {
        Path srcDir = tempDir.resolve("src/main/java");
        Files.createDirectories(srcDir);

        createFile(srcDir.resolve("App.java"), "public class App {}");
        createFile(tempDir.resolve("pom.xml"), "<project><modelVersion>4.0.0</modelVersion></project>");
        createFile(srcDir.resolve("util.py"), "def hello(): pass");
        createFile(tempDir.resolve("Dockerfile"), "FROM openjdk:17");
        createFile(tempDir.resolve("README.md"), "# Project");
        createFile(tempDir.resolve("poetry.lock"), "hash = abc123");

        originalCacheKey = computeCacheKey();
    }

    @When("I modify a Java source file")
    public void iModifyAJavaSourceFile() throws IOException, NoSuchAlgorithmException {
        Path javaFile = tempDir.resolve("src/main/java/App.java");
        Files.write(javaFile, "public class App { int x = 1; }".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @When("I modify the pom.xml file")
    public void iModifyThePomXmlFile() throws IOException, NoSuchAlgorithmException {
        Path pomFile = tempDir.resolve("pom.xml");
        Files.write(pomFile, "<project><modelVersion>4.0.0</modelVersion><version>2.0</version></project>".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @When("I modify a non-tracked file like {string}")
    public void iModifyANonTrackedFileLike(String filename) throws IOException, NoSuchAlgorithmException {
        Path file = tempDir.resolve(filename);
        Files.write(file, "# Updated README content".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @When("I modify a Python source file")
    public void iModifyAPythonSourceFile() throws IOException, NoSuchAlgorithmException {
        Path pyFile = tempDir.resolve("src/main/java/util.py");
        Files.write(pyFile, "def hello(): return 'world'".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @When("I modify a Dockerfile")
    public void iModifyADockerfile() throws IOException, NoSuchAlgorithmException {
        Path dockerfile = tempDir.resolve("Dockerfile");
        Files.write(dockerfile, "FROM openjdk:21-slim".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @When("I modify the {string} file")
    public void iModifyTheFile(String filename) throws IOException, NoSuchAlgorithmException {
        Path file = tempDir.resolve(filename);
        Files.write(file, "modified-content-here".getBytes(StandardCharsets.UTF_8));
        currentCacheKey = computeCacheKey();
    }

    @Then("the computed cache key should differ from the original")
    public void theComputedCacheKeyShouldDifferFromTheOriginal() {
        assertNotEquals("Cache key should change after tracked file modification", originalCacheKey, currentCacheKey);
    }

    @Then("the computed cache key should match the original")
    public void theComputedCacheKeyShouldMatchTheOriginal() {
        assertEquals("Cache key should remain stable for non-tracked file changes", originalCacheKey, currentCacheKey);
    }

    private String computeCacheKey() throws IOException, NoSuchAlgorithmException {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        computeDigestForDirectory(tempDir.toFile(), digest);
        byte[] hash = digest.digest();
        StringBuilder hexString = new StringBuilder();
        for (byte b : hash) {
            String hex = Integer.toHexString(0xff & b);
            if (hex.length() == 1) {
                hexString.append('0');
            }
            hexString.append(hex);
        }
        return hexString.toString();
    }

    private void computeDigestForDirectory(File dir, MessageDigest digest) throws IOException {
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        Arrays.sort(files);
        for (File file : files) {
            if (file.isDirectory()) {
                computeDigestForDirectory(file, digest);
            } else if (isTrackedFile(file)) {
                byte[] content = Files.readAllBytes(file.toPath());
                digest.update(file.getName().getBytes(StandardCharsets.UTF_8));
                digest.update(content);
            }
        }
    }

    private boolean isTrackedFile(File file) {
        String name = file.getName();

        if (EXCLUDED_FILES.contains(name)) {
            return false;
        }

        if (TRACKED_FILENAMES.contains(name)) {
            return true;
        }

        for (String ext : TRACKED_EXTENSIONS) {
            if (name.endsWith(ext)) {
                return true;
            }
        }

        return false;
    }

    private void createFile(Path path, String content) throws IOException {
        Files.createDirectories(path.getParent());
        Files.write(path, content.getBytes(StandardCharsets.UTF_8));
    }
}
