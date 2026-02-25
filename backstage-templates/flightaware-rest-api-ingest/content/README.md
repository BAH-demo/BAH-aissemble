# ${{ values.componentName }}

${{ values.description }}

## Overview

This project implements a data ingest pipeline that retrieves flight data from
the [FlightAware AeroAPI v4](https://www.flightaware.com/aeroapi/portal) and
persists it using the **aiSSEMBLE** data-delivery framework.

| Setting              | Value                                      |
| -------------------- | ------------------------------------------ |
| API Endpoint         | `${{ values.flightawareApiEndpoint }}`     |
| Polling Interval     | `${{ values.pollingIntervalSeconds }}` sec |
| Persistence Target   | `${{ values.persistenceType }}`            |
| Data Lineage         | `${{ values.enableDataLineage }}`          |
| Alerting             | `${{ values.enableAlerting }}`             |

## Project Structure

```
.
├── catalog-info.yaml              # Backstage catalog descriptor
├── docker/
│   └── Dockerfile                 # Container image for the ingest pipeline
├── pipeline-models/
│   └── src/main/resources/
│       ├── pipelines/             # aiSSEMBLE pipeline model definitions
│       ├── records/               # Record (schema) definitions
│       └── dictionaries/          # Dictionary type definitions
└── pipelines/
    └── src/main/python/
        ├── flightaware_ingest.py  # Core ingest logic (fetch, transform, load)
        ├── flightaware_config.py  # Centralised configuration
        └── requirements.txt       # Python dependencies
```

## Prerequisites

1. **FlightAware AeroAPI key** -- sign up at
   <https://www.flightaware.com/aeroapi/portal> and set the
   `FLIGHTAWARE_API_KEY` environment variable.
2. **aiSSEMBLE** toolchain -- see the
   [developer docs](https://boozallen.github.io/aissemble/current/index.html).
3. **Apache Spark** runtime (provided by the aiSSEMBLE Docker images).

## Quick Start

```bash
# Export your API key
export FLIGHTAWARE_API_KEY="your-key-here"

# Build with Maven (generates code from the pipeline models)
./mvnw clean install

# Run locally via Docker Compose (if configured)
docker compose up --build
```

## Configuration

All runtime settings can be overridden through environment variables:

| Variable                     | Description                          | Default                                          |
| ---------------------------- | ------------------------------------ | ------------------------------------------------ |
| `FLIGHTAWARE_API_KEY`        | AeroAPI authentication key           | *(required)*                                     |
| `FLIGHTAWARE_BASE_URL`       | AeroAPI base URL                     | `${{ values.flightawareApiBaseUrl }}`            |
| `FLIGHTAWARE_ENDPOINT`       | API resource path                    | `${{ values.flightawareApiEndpoint }}`           |
| `POLLING_INTERVAL_SECONDS`   | Seconds between API poll cycles      | `${{ values.pollingIntervalSeconds }}`           |

## Pipeline Steps

1. **FetchFlightData** -- calls the AeroAPI endpoint with pagination support.
2. **TransformFlightData** -- normalises the raw JSON into a flat PySpark
   DataFrame matching the `FlightRecord` / `FlightPositionRecord` schemas.
3. **PersistFlightData** -- writes the DataFrame to the configured
   `${{ values.persistenceType }}` store.
