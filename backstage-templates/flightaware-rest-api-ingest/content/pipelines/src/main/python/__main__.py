"""
Entrypoint for the FlightAware data ingest pipeline.

Reads configuration from environment variables, initialises a SparkSession,
and starts the polling loop that periodically fetches flight data from the
FlightAware AeroAPI and persists it.
"""

import logging
import os
import sys

from pyspark.sql import SparkSession

from flightaware_config import (
    FLIGHTAWARE_API_KEY,
    FLIGHTAWARE_ENDPOINT,
    PIPELINE_NAME,
    POLLING_INTERVAL_SECONDS,
)
from flightaware_ingest import run_polling_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    if not FLIGHTAWARE_API_KEY:
        logger.error(
            "FLIGHTAWARE_API_KEY environment variable is not set. "
            "Please provide your AeroAPI key to start the ingest pipeline."
        )
        sys.exit(1)

    spark = (
        SparkSession.builder.appName(PIPELINE_NAME)
        .getOrCreate()
    )

    logger.info(
        "Starting %s  endpoint=%s  interval=%ds",
        PIPELINE_NAME,
        FLIGHTAWARE_ENDPOINT,
        POLLING_INTERVAL_SECONDS,
    )

    try:
        run_polling_loop(
            spark=spark,
            api_key=FLIGHTAWARE_API_KEY,
            endpoint=FLIGHTAWARE_ENDPOINT,
            interval=POLLING_INTERVAL_SECONDS,
        )
    except KeyboardInterrupt:
        logger.info("Shutting down %s", PIPELINE_NAME)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
