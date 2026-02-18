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
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;

import org.w3c.dom.Document;
import org.w3c.dom.NodeList;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

public class BuildCacheDockerFreshnessSteps {

    private static final String CACHE_CONFIG_PATH = findProjectRoot() + "/.mvn/maven-build-cache-config.xml";
    private static final String ARCHETYPE_CONFIG_PATH = findProjectRoot()
            + "/foundation/foundation-archetype/src/main/resources/archetype-resources/.mvn/maven-build-cache-config.xml";

    private Document cacheConfigDoc;
    private Document archetypeConfigDoc;
    private String rawContent;

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

    @When("I read the local cache settings")
    public void iReadTheLocalCacheSettings() throws Exception {
        File configFile = new File(CACHE_CONFIG_PATH);
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        cacheConfigDoc = builder.parse(configFile);
    }

    @Then("only {int} build should be cached")
    public void onlyBuildShouldBeCached(int expected) {
        NodeList nodes = cacheConfigDoc.getElementsByTagNameNS("*", "maxBuildsCached");
        if (nodes.getLength() == 0) {
            nodes = cacheConfigDoc.getElementsByTagName("maxBuildsCached");
        }
        assertTrue("maxBuildsCached element should exist", nodes.getLength() > 0);
        assertEquals("Max builds cached should be " + expected, String.valueOf(expected), nodes.item(0).getTextContent().trim());
    }

    @When("I read the raw configuration content")
    public void iReadTheRawConfigurationContent() throws Exception {
        rawContent = new String(Files.readAllBytes(Paths.get(CACHE_CONFIG_PATH)), StandardCharsets.UTF_8);
    }

    @Then("the configuration should contain a comment about stale docker images")
    public void theConfigurationShouldContainACommentAboutStaleDockerImages() {
        assertNotNull("Raw content should not be null", rawContent);
        assertTrue("Configuration should mention stale docker images",
                rawContent.toLowerCase().contains("stale docker images"));
    }

    @Given("the archetype Maven build cache configuration file exists")
    public void theArchetypeMavenBuildCacheConfigurationFileExists() {
        File archetypeConfig = new File(ARCHETYPE_CONFIG_PATH);
        assertTrue("Archetype cache config should exist at: " + ARCHETYPE_CONFIG_PATH, archetypeConfig.exists());
    }

    @When("I read the archetype cache configuration")
    public void iReadTheArchetypeCacheConfiguration() throws Exception {
        File archetypeConfig = new File(ARCHETYPE_CONFIG_PATH);
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setNamespaceAware(true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        archetypeConfigDoc = builder.parse(archetypeConfig);
    }

    @Then("the archetype maximum builds cached should be {int}")
    public void theArchetypeMaximumBuildsCachedShouldBe(int expected) {
        NodeList nodes = archetypeConfigDoc.getElementsByTagNameNS("*", "maxBuildsCached");
        if (nodes.getLength() == 0) {
            nodes = archetypeConfigDoc.getElementsByTagName("maxBuildsCached");
        }
        assertTrue("Archetype maxBuildsCached element should exist", nodes.getLength() > 0);
        assertEquals("Archetype max builds cached should be " + expected,
                String.valueOf(expected), nodes.item(0).getTextContent().trim());
    }
}
