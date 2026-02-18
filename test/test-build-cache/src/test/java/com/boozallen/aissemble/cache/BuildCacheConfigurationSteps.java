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
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

public class BuildCacheConfigurationSteps {

    private static final String CACHE_CONFIG_PATH = findProjectRoot() + "/.mvn/maven-build-cache-config.xml";

    private Document cacheConfigDoc;
    private File configFile;

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

    @Given("the Maven build cache configuration file exists")
    public void theMavenBuildCacheConfigurationFileExists() {
        configFile = new File(CACHE_CONFIG_PATH);
        assertTrue("Cache config file should exist at: " + CACHE_CONFIG_PATH, configFile.exists());
    }

    @When("I read the cache configuration")
    public void iReadTheCacheConfiguration() throws Exception {
        cacheConfigDoc = parseXml(configFile);
        assertNotNull("Cache config document should be parsed", cacheConfigDoc);
    }

    @Then("the build cache should be enabled")
    public void theBuildCacheShouldBeEnabled() {
        String enabled = getElementText(cacheConfigDoc, "enabled");
        assertEquals("Build cache should be enabled", "true", enabled);
    }

    @Then("the hash algorithm should be {string}")
    public void theHashAlgorithmShouldBe(String expected) {
        String hashAlgorithm = getElementText(cacheConfigDoc, "hashAlgorithm");
        assertEquals("Hash algorithm mismatch", expected, hashAlgorithm);
    }

    @Then("XML validation should be enabled")
    public void xmlValidationShouldBeEnabled() {
        String validateXml = getElementText(cacheConfigDoc, "validateXml");
        assertEquals("XML validation should be enabled", "true", validateXml);
    }

    @Then("the remote cache should be disabled")
    public void theRemoteCacheShouldBeDisabled() {
        NodeList remoteNodes = cacheConfigDoc.getElementsByTagName("remote");
        assertTrue("Remote element should exist", remoteNodes.getLength() > 0);
        Element remote = (Element) remoteNodes.item(0);
        String enabled = remote.getAttribute("enabled");
        assertEquals("Remote cache should be disabled", "false", enabled);
    }

    @Then("the maximum builds cached should be {int}")
    public void theMaximumBuildsCachedShouldBe(int expected) {
        String maxBuilds = getElementText(cacheConfigDoc, "maxBuildsCached");
        assertEquals("Max builds cached mismatch", String.valueOf(expected), maxBuilds);
    }

    @Then("the cache input should include {string}")
    public void theCacheInputShouldInclude(String expected) {
        NodeList includeNodes = cacheConfigDoc.getElementsByTagName("include");
        boolean found = false;
        for (int i = 0; i < includeNodes.getLength(); i++) {
            if (includeNodes.item(i).getTextContent().trim().equals(expected)) {
                found = true;
                break;
            }
        }
        assertTrue("Cache input should include: " + expected, found);
    }

    @Then("the cache glob should include {string}")
    public void theCacheGlobShouldInclude(String expected) {
        String glob = getElementText(cacheConfigDoc, "glob");
        assertNotNull("Glob pattern should exist", glob);
        assertTrue("Glob should include: " + expected, glob.contains(expected));
    }

    @Then("the {string} goal {string} should always run")
    public void theGoalShouldAlwaysRun(String artifactId, String goalName) {
        NodeList goalsListNodes = cacheConfigDoc.getElementsByTagName("goalsList");
        boolean found = false;
        for (int i = 0; i < goalsListNodes.getLength(); i++) {
            Element goalsList = (Element) goalsListNodes.item(i);
            if (artifactId.equals(goalsList.getAttribute("artifactId"))) {
                NodeList goals = goalsList.getElementsByTagName("goal");
                for (int j = 0; j < goals.getLength(); j++) {
                    if (goalName.equals(goals.item(j).getTextContent().trim())) {
                        found = true;
                        break;
                    }
                }
            }
        }
        assertTrue("Goal " + goalName + " of " + artifactId + " should always run", found);
    }

    private Document parseXml(File file) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        return builder.parse(file);
    }

    private String getElementText(Document doc, String tagName) {
        NodeList nodes = doc.getElementsByTagNameNS("*", tagName);
        if (nodes.getLength() == 0) {
            nodes = doc.getElementsByTagName(tagName);
        }
        if (nodes.getLength() > 0) {
            return nodes.item(0).getTextContent().trim();
        }
        return null;
    }
}
