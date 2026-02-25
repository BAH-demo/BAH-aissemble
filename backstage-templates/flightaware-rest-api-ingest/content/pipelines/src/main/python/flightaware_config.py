"""
FlightAware Pipeline Configuration
====================================

Centralised configuration for the FlightAware data ingest pipeline.
Values prefixed with ``${{`` are resolved at scaffolding time by the
Backstage template engine.  At runtime the pipeline reads its API key
from the environment (or the aiSSEMBLE configuration store).
"""

import os

# ---------------------------------------------------------------------------
# FlightAware AeroAPI settings
# ---------------------------------------------------------------------------
FLIGHTAWARE_API_KEY: str = os.environ.get("FLIGHTAWARE_API_KEY", "")
FLIGHTAWARE_BASE_URL: str = os.environ.get(
    "FLIGHTAWARE_BASE_URL",
    "${{ values.flightawareApiBaseUrl }}",
)
FLIGHTAWARE_ENDPOINT: str = os.environ.get(
    "FLIGHTAWARE_ENDPOINT",
    "${{ values.flightawareApiEndpoint }}",
)
POLLING_INTERVAL_SECONDS: int = int(
    os.environ.get("POLLING_INTERVAL_SECONDS", "${{ values.pollingIntervalSeconds }}")
)

# ---------------------------------------------------------------------------
# Persistence settings
# ---------------------------------------------------------------------------
PERSISTENCE_TYPE: str = "${{ values.persistenceType }}"

# ---------------------------------------------------------------------------
# Spark / pipeline metadata
# ---------------------------------------------------------------------------
PIPELINE_NAME: str = "FlightAwareIngestPipeline"
JAVA_PACKAGE: str = "${{ values.javaPackage }}"
