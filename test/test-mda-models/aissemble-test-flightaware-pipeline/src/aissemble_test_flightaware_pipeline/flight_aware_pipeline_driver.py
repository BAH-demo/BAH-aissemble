###
# #%L
# aiSSEMBLE::Test::MDA::FlightAware Pipeline
# %%
# Copyright (C) 2021 Booz Allen
# %%
# This software package is licensed under the Booz Allen Public License.
# All Rights Reserved. You may not copy, reproduce, distribute, publish,
# display, execute, modify, create derivative works of, transmit, sell or
# offer for resale, or in any way exploit any part of this solution without
# Booz Allen Hamilton's express written permission.
# #L%
###
from aissemble_test_flightaware_pipeline.step.ingest import Ingest
from krausening.logging import LogManager

"""
Driver to run the FlightAwarePipeline.

GENERATED STUB CODE - PLEASE ***DO*** MODIFY

Originally generated from: templates/data-delivery-pyspark/pipeline.driver.py.vm
"""

logger = LogManager.get_instance().get_logger('FlightAwarePipeline')

if __name__ == "__main__":
    logger.info('STARTED: FlightAwarePipeline driver')

    # Execute the Ingest step to pull data from FlightAware API and persist to Delta Lake
    Ingest().execute_step()
