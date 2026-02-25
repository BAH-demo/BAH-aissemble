# FlightAware Pipeline Test Model

This module contains a FlightAware API data pipeline model that uses PySpark with Delta Lake persistence. It demonstrates pulling hourly flight data from the FlightAware AeroAPI and persisting it to Delta Lake.

## Pipeline Overview

- **Pipeline Name:** FlightAwarePipeline
- **Implementation:** data-delivery-pyspark
- **Step:** Ingest (synchronous, Delta Lake persistence)
- **Scheduling:** Airflow (hourly)
