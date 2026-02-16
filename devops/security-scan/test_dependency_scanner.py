"""
Tests for Dependency Vulnerability Scanner.
"""

import os
import tempfile
import json
import pytest
from dependency_scanner import (
    parse_maven_pom,
    parse_requirements_txt,
    parse_pyproject_toml,
    scan_directory_for_deps,
    generate_json_report,
    generate_markdown_report,
    load_allowlist,
)


@pytest.fixture
def sample_pom():
    content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <properties>
        <version.quarkus>3.15.6</version.quarkus>
    </properties>
    <dependencies>
        <dependency>
            <groupId>io.quarkus</groupId>
            <artifactId>quarkus-core</artifactId>
            <version>${version.quarkus}</version>
        </dependency>
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>3.14.0</version>
        </dependency>
    </dependencies>
</project>'''
    fd, path = tempfile.mkstemp(suffix=".xml")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.fixture
def sample_requirements():
    content = '''requests>=2.31.0
flask==3.0.0
numpy>=1.24.0,<2.0
# comment line
-r base-requirements.txt
pandas==2.1.0
'''
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


@pytest.fixture
def sample_pyproject():
    content = '''[tool.poetry.dependencies]
requests = ">=2.32.2"
cryptography = ">=43.0.0"
pydantic = "^2.0"
'''
    fd, path = tempfile.mkstemp(suffix=".toml")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


class TestMavenPomParsing:
    def test_parse_dependencies(self, sample_pom):
        deps = parse_maven_pom(sample_pom)
        assert len(deps) == 2
        os.unlink(sample_pom)

    def test_property_resolution(self, sample_pom):
        deps = parse_maven_pom(sample_pom)
        quarkus_dep = next(d for d in deps if d["artifact_id"] == "quarkus-core")
        assert quarkus_dep["version"] == "3.15.6"
        os.unlink(sample_pom)

    def test_direct_version(self, sample_pom):
        deps = parse_maven_pom(sample_pom)
        commons_dep = next(d for d in deps if d["artifact_id"] == "commons-lang3")
        assert commons_dep["version"] == "3.14.0"
        os.unlink(sample_pom)

    def test_ecosystem_is_maven(self, sample_pom):
        deps = parse_maven_pom(sample_pom)
        for dep in deps:
            assert dep["ecosystem"] == "maven"
        os.unlink(sample_pom)


class TestRequirementsParsing:
    def test_parse_requirements(self, sample_requirements):
        deps = parse_requirements_txt(sample_requirements)
        assert len(deps) >= 3
        os.unlink(sample_requirements)

    def test_skips_comments(self, sample_requirements):
        deps = parse_requirements_txt(sample_requirements)
        names = [d["name"] for d in deps]
        assert "#" not in str(names)
        os.unlink(sample_requirements)

    def test_ecosystem_is_pypi(self, sample_requirements):
        deps = parse_requirements_txt(sample_requirements)
        for dep in deps:
            assert dep["ecosystem"] == "pypi"
        os.unlink(sample_requirements)


class TestPyprojectParsing:
    def test_parse_pyproject(self, sample_pyproject):
        deps = parse_pyproject_toml(sample_pyproject)
        assert len(deps) >= 2
        os.unlink(sample_pyproject)


class TestDirectoryScanning:
    def test_scan_mixed_project(self):
        tmpdir = tempfile.mkdtemp()
        with open(os.path.join(tmpdir, "pom.xml"), "w") as f:
            f.write('''<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <dependencies>
        <dependency>
            <groupId>org.test</groupId>
            <artifactId>test-lib</artifactId>
            <version>1.0.0</version>
        </dependency>
    </dependencies>
</project>''')
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("flask==3.0.0\n")
        deps = scan_directory_for_deps(tmpdir)
        assert len(deps) >= 2
        ecosystems = {d["ecosystem"] for d in deps}
        assert "maven" in ecosystems
        assert "pypi" in ecosystems


class TestReportGeneration:
    def test_json_report(self):
        output_dir = tempfile.mkdtemp()
        deps = [{"ecosystem": "maven", "group_id": "org.test", "artifact_id": "test", "version": "1.0", "source_file": "pom.xml"}]
        vulns = [{"cve_id": "CVE-2024-0001", "severity": "HIGH", "cvss_score": 8.5, "component": "test"}]
        generate_json_report(deps, vulns, {}, os.path.join(output_dir, "report.json"))
        with open(os.path.join(output_dir, "report.json")) as f:
            report = json.load(f)
        assert report["total_dependencies"] == 1
        assert report["total_vulnerabilities"] == 1

    def test_markdown_report(self):
        output_dir = tempfile.mkdtemp()
        deps = [{"ecosystem": "maven", "group_id": "org.test", "artifact_id": "test", "version": "1.0", "source_file": "pom.xml"}]
        vulns = [{"cve_id": "CVE-2024-0001", "severity": "HIGH", "cvss_score": 8.5, "component": "test"}]
        generate_markdown_report(deps, vulns, {}, os.path.join(output_dir, "report.md"))
        with open(os.path.join(output_dir, "report.md")) as f:
            content = f.read()
        assert "CVE-2024-0001" in content
        assert "HIGH" in content


class TestAllowlist:
    def test_load_empty_allowlist(self):
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w") as f:
            f.write("allowed_cves: []\n")
        result = load_allowlist(path)
        assert len(result) == 0
        os.unlink(path)

    def test_nonexistent_allowlist(self):
        result = load_allowlist("/nonexistent/path.yaml")
        assert len(result) == 0
