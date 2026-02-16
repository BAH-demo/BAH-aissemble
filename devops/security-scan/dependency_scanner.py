#!/usr/bin/env python3
"""
Dependency Vulnerability Scanner for aiSSEMBLE Platform.
Parses Maven pom.xml and Python dependency files, checks against NVD API.
Generates structured vulnerability reports in JSON and Markdown formats.

Usage:
    python dependency_scanner.py --scan-dir /path/to/project [--output-dir ./reports]
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
MAVEN_NS = "{http://maven.apache.org/POM/4.0.0}"


def parse_maven_pom(pom_path: str) -> List[Dict[str, str]]:
    dependencies = []
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        properties = {}
        props_elem = root.find(f"{MAVEN_NS}properties")
        if props_elem is not None:
            for prop in props_elem:
                tag = prop.tag.replace(MAVEN_NS, "")
                properties[tag] = prop.text or ""

        for dep in root.iter(f"{MAVEN_NS}dependency"):
            group_id = dep.find(f"{MAVEN_NS}groupId")
            artifact_id = dep.find(f"{MAVEN_NS}artifactId")
            version = dep.find(f"{MAVEN_NS}version")
            if group_id is not None and artifact_id is not None:
                ver_text = ""
                if version is not None and version.text:
                    ver_text = version.text
                    prop_match = re.match(r"\$\{(.+)\}", ver_text)
                    if prop_match:
                        ver_text = properties.get(prop_match.group(1), ver_text)
                dependencies.append({
                    "ecosystem": "maven",
                    "group_id": group_id.text or "",
                    "artifact_id": artifact_id.text or "",
                    "version": ver_text,
                    "source_file": str(pom_path),
                })
    except ET.ParseError:
        print(f"WARNING: Failed to parse {pom_path}", file=sys.stderr)
    return dependencies


def parse_requirements_txt(req_path: str) -> List[Dict[str, str]]:
    dependencies = []
    try:
        with open(req_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([><=!~]+\s*.+)?$", line)
                if match:
                    name = match.group(1)
                    version = match.group(2) or ""
                    version = re.sub(r"[><=!~^]+\s*", "", version).strip().split(",")[0]
                    dependencies.append({
                        "ecosystem": "pypi",
                        "name": name,
                        "version": version,
                        "source_file": str(req_path),
                    })
    except OSError:
        print(f"WARNING: Failed to read {req_path}", file=sys.stderr)
    return dependencies


def parse_pyproject_toml(toml_path: str) -> List[Dict[str, str]]:
    dependencies = []
    try:
        with open(toml_path, "r", encoding="utf-8") as f:
            content = f.read()
        dep_sections = re.findall(
            r'\[(?:tool\.poetry\.dependencies|project\.dependencies)\](.*?)(?=\n\[|\Z)',
            content, re.DOTALL,
        )
        for section in dep_sections:
            for line in section.strip().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^([a-zA-Z0-9_\-]+)\s*=\s*["\']?([^"\']+)', line)
                if match:
                    name = match.group(1)
                    if name.lower() in ("python", "python_requires"):
                        continue
                    version = match.group(2).strip().rstrip('"').rstrip("'")
                    version = re.sub(r"[><=!~^]+", "", version).strip().split(",")[0]
                    dependencies.append({
                        "ecosystem": "pypi",
                        "name": name,
                        "version": version,
                        "source_file": str(toml_path),
                    })
    except OSError:
        print(f"WARNING: Failed to read {toml_path}", file=sys.stderr)
    return dependencies


def scan_directory_for_deps(scan_dir: str) -> List[Dict[str, str]]:
    all_deps = []
    root = Path(scan_dir)
    excluded_dirs = {".git", "node_modules", "__pycache__", "target", ".tox"}

    for pom in root.rglob("pom.xml"):
        if any(p in pom.parts for p in excluded_dirs):
            continue
        all_deps.extend(parse_maven_pom(str(pom)))

    for req in root.rglob("requirements*.txt"):
        if any(p in req.parts for p in excluded_dirs):
            continue
        all_deps.extend(parse_requirements_txt(str(req)))

    for toml in root.rglob("pyproject.toml"):
        if any(p in toml.parts for p in excluded_dirs):
            continue
        all_deps.extend(parse_pyproject_toml(str(toml)))

    return all_deps


def check_nvd_cves(keyword: str, api_key: str = "") -> List[Dict[str, Any]]:
    params = f"?keywordSearch={urllib.request.quote(keyword)}&resultsPerPage=5"
    url = NVD_API_URL + params
    headers = {"Accept": "application/json"}
    if api_key:
        headers["apiKey"] = api_key

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        cves = []
        for vuln in data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            cve_id = cve.get("id", "")
            descriptions = cve.get("descriptions", [])
            desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")
            metrics = cve.get("metrics", {})
            score = 0.0
            severity = "UNKNOWN"
            for metric_key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                metric_list = metrics.get(metric_key, [])
                if metric_list:
                    cvss_data = metric_list[0].get("cvssData", {})
                    score = cvss_data.get("baseScore", 0.0)
                    severity = cvss_data.get("baseSeverity", "UNKNOWN")
                    break
            cves.append({
                "cve_id": cve_id,
                "description": desc[:200],
                "cvss_score": score,
                "severity": severity,
            })
        return cves
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        return []


def load_allowlist(allowlist_path: str) -> Dict[str, Dict[str, str]]:
    allowlist = {}
    if not Path(allowlist_path).exists():
        return allowlist
    try:
        import yaml
        with open(allowlist_path, "r") as f:
            data = yaml.safe_load(f)
        if data and isinstance(data, dict):
            for entry in data.get("allowed_cves", []):
                cve_id = entry.get("cve_id", "")
                expiration = entry.get("expiration_date", "")
                if expiration:
                    exp_date = datetime.strptime(expiration, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if exp_date < datetime.now(timezone.utc):
                        continue
                allowlist[cve_id] = entry
    except ImportError:
        try:
            with open(allowlist_path, "r") as f:
                content = f.read()
            for match in re.finditer(r"cve_id:\s*(\S+)", content):
                allowlist[match.group(1)] = {"cve_id": match.group(1)}
        except OSError:
            pass
    except OSError:
        pass
    return allowlist


def generate_json_report(
    dependencies: List[Dict[str, str]],
    vulnerabilities: List[Dict[str, Any]],
    allowlist: Dict[str, Dict[str, str]],
    output_path: str,
) -> None:
    report = {
        "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_dependencies": len(dependencies),
        "total_vulnerabilities": len(vulnerabilities),
        "allowlisted_count": sum(1 for v in vulnerabilities if v.get("cve_id") in allowlist),
        "dependencies": dependencies,
        "vulnerabilities": vulnerabilities,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"JSON report written to {output_path}")


def generate_markdown_report(
    dependencies: List[Dict[str, str]],
    vulnerabilities: List[Dict[str, Any]],
    allowlist: Dict[str, Dict[str, str]],
    output_path: str,
) -> None:
    lines = [
        "# Dependency Vulnerability Scan Report",
        "",
        f"**Scan Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Total Dependencies Scanned:** {len(dependencies)}",
        f"**Vulnerabilities Found:** {len(vulnerabilities)}",
        f"**Allowlisted:** {sum(1 for v in vulnerabilities if v.get('cve_id') in allowlist)}",
        "",
        "## Vulnerability Summary",
        "",
    ]

    if vulnerabilities:
        lines.append("| CVE ID | Severity | CVSS Score | Component | Status |")
        lines.append("|--------|----------|------------|-----------|--------|")
        for vuln in sorted(vulnerabilities, key=lambda v: v.get("cvss_score", 0), reverse=True):
            cve_id = vuln.get("cve_id", "N/A")
            severity = vuln.get("severity", "UNKNOWN")
            score = vuln.get("cvss_score", 0.0)
            component = vuln.get("component", "N/A")
            status = "ALLOWLISTED" if cve_id in allowlist else "OPEN"
            lines.append(f"| {cve_id} | {severity} | {score} | {component} | {status} |")
    else:
        lines.append("No vulnerabilities found.")

    lines.extend([
        "",
        "## Dependencies",
        "",
        f"Total: {len(dependencies)}",
        "",
    ])

    maven_deps = [d for d in dependencies if d.get("ecosystem") == "maven"]
    pypi_deps = [d for d in dependencies if d.get("ecosystem") == "pypi"]

    if maven_deps:
        lines.append(f"### Maven Dependencies ({len(maven_deps)})")
        lines.append("")
        lines.append("| Group ID | Artifact ID | Version | Source |")
        lines.append("|----------|-------------|---------|--------|")
        for dep in maven_deps[:50]:
            lines.append(
                f"| {dep.get('group_id', '')} | {dep.get('artifact_id', '')} "
                f"| {dep.get('version', '')} | {dep.get('source_file', '')} |"
            )

    if pypi_deps:
        lines.append(f"\n### Python Dependencies ({len(pypi_deps)})")
        lines.append("")
        lines.append("| Package | Version | Source |")
        lines.append("|---------|---------|--------|")
        for dep in pypi_deps[:50]:
            lines.append(
                f"| {dep.get('name', '')} | {dep.get('version', '')} "
                f"| {dep.get('source_file', '')} |"
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Markdown report written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Dependency Vulnerability Scanner")
    parser.add_argument("--scan-dir", required=True, help="Directory to scan")
    parser.add_argument("--output-dir", default="./reports", help="Output directory for reports")
    parser.add_argument("--allowlist", default=".security-allowlist.yaml", help="Path to allowlist file")
    parser.add_argument("--nvd-api-key", default="", help="NVD API key for higher rate limits")
    parser.add_argument("--skip-nvd", action="store_true", help="Skip NVD API checks (offline mode)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {args.scan_dir} for dependencies...")
    dependencies = scan_directory_for_deps(args.scan_dir)
    print(f"Found {len(dependencies)} dependencies")

    allowlist = load_allowlist(args.allowlist)
    print(f"Loaded {len(allowlist)} allowlisted CVEs")

    vulnerabilities: List[Dict[str, Any]] = []
    if not args.skip_nvd:
        checked = set()
        for dep in dependencies:
            keyword = dep.get("artifact_id") or dep.get("name", "")
            if keyword and keyword not in checked:
                checked.add(keyword)
                cves = check_nvd_cves(keyword, args.nvd_api_key)
                for cve in cves:
                    cve["component"] = keyword
                    cve["version"] = dep.get("version", "")
                    vulnerabilities.append(cve)
    else:
        print("Skipping NVD API checks (offline mode)")

    generate_json_report(
        dependencies, vulnerabilities, allowlist,
        str(output_dir / "vulnerability-report.json"),
    )
    generate_markdown_report(
        dependencies, vulnerabilities, allowlist,
        str(output_dir / "vulnerability-report.md"),
    )

    open_vulns = [v for v in vulnerabilities if v.get("cve_id") not in allowlist]
    critical_count = sum(1 for v in open_vulns if v.get("severity") == "CRITICAL")
    high_count = sum(1 for v in open_vulns if v.get("severity") == "HIGH")
    print(f"\nScan complete: {len(open_vulns)} open vulnerabilities "
          f"({critical_count} critical, {high_count} high)")
    return 1 if critical_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
