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
from ..generated.step.ingest_base import IngestBase
from krausening.logging import LogManager
from krausening.properties import PropertyManager

import requests
from pyspark.sql import Row
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    BooleanType,
)
from datetime import datetime, timezone


class Ingest(IngestBase):
    """
    Performs the business logic for Ingest.

    Pulls flight data from the FlightAware AeroAPI and persists it to Delta Lake.

    GENERATED STUB CODE - PLEASE ***DO*** MODIFY

    Originally generated from: templates/data-delivery-pyspark/synchronous.processor.impl.py.vm
    """

    logger = LogManager.get_instance().get_logger('Ingest')

    # FlightAware AeroAPI base URL
    AEROAPI_BASE_URL = "https://aeroapi.flightaware.com/aeroapi"

    # Delta Lake table name for flight data
    FLIGHT_TABLE_NAME = "flightaware_flights"

    # Schema for the flight data DataFrame
    FLIGHT_SCHEMA = StructType([
        StructField("ident", StringType(), True),
        StructField("ident_icao", StringType(), True),
        StructField("ident_iata", StringType(), True),
        StructField("fa_flight_id", StringType(), True),
        StructField("operator", StringType(), True),
        StructField("operator_icao", StringType(), True),
        StructField("operator_iata", StringType(), True),
        StructField("flight_number", StringType(), True),
        StructField("registration", StringType(), True),
        StructField("atc_ident", StringType(), True),
        StructField("inbound_fa_flight_id", StringType(), True),
        StructField("codeshares", StringType(), True),
        StructField("codeshares_iata", StringType(), True),
        StructField("blocked", BooleanType(), True),
        StructField("diverted", BooleanType(), True),
        StructField("cancelled", BooleanType(), True),
        StructField("position_only", BooleanType(), True),
        StructField("origin_code", StringType(), True),
        StructField("origin_name", StringType(), True),
        StructField("origin_city", StringType(), True),
        StructField("destination_code", StringType(), True),
        StructField("destination_name", StringType(), True),
        StructField("destination_city", StringType(), True),
        StructField("departure_time", StringType(), True),
        StructField("arrival_time", StringType(), True),
        StructField("filed_ete", IntegerType(), True),
        StructField("progress_percent", IntegerType(), True),
        StructField("status", StringType(), True),
        StructField("aircraft_type", StringType(), True),
        StructField("route_distance", IntegerType(), True),
        StructField("filed_airspeed", IntegerType(), True),
        StructField("filed_altitude", IntegerType(), True),
        StructField("route", StringType(), True),
        StructField("baggage_claim", StringType(), True),
        StructField("seats_cabin_business", IntegerType(), True),
        StructField("seats_cabin_coach", IntegerType(), True),
        StructField("seats_cabin_first", IntegerType(), True),
        StructField("gate_origin", StringType(), True),
        StructField("gate_destination", StringType(), True),
        StructField("terminal_origin", StringType(), True),
        StructField("terminal_destination", StringType(), True),
        StructField("type", StringType(), True),
        StructField("scheduled_out", StringType(), True),
        StructField("estimated_out", StringType(), True),
        StructField("actual_out", StringType(), True),
        StructField("scheduled_off", StringType(), True),
        StructField("estimated_off", StringType(), True),
        StructField("actual_off", StringType(), True),
        StructField("scheduled_on", StringType(), True),
        StructField("estimated_on", StringType(), True),
        StructField("actual_on", StringType(), True),
        StructField("scheduled_in", StringType(), True),
        StructField("estimated_in", StringType(), True),
        StructField("actual_in", StringType(), True),
        StructField("ingestion_timestamp", StringType(), True),
    ])

    def __init__(self):
        super().__init__('synchronous', self.get_data_action_descriptive_label())

    def get_data_action_descriptive_label(self) -> str:
        """
        Provides a descriptive label for the action that can be used for logging (e.g., provenance details).
        """
        return 'FlightAwareIngest'

    def execute_step_impl(self):
        """
        This method performs the business logic of this step.

        It calls the FlightAware AeroAPI to fetch current flight data,
        converts the response into a Spark DataFrame, and persists it
        to Delta Lake using the inherited save_dataset method.
        """
        Ingest.logger.info('Starting FlightAware data ingestion...')

        api_key = self._get_api_key()
        if not api_key:
            Ingest.logger.error(
                'FlightAware API key not configured. '
                'Please set it via the Configuration Store or Sealed Secrets.'
            )
            return

        flights = self._fetch_flights(api_key)
        if not flights:
            Ingest.logger.warn('No flight data returned from FlightAware API.')
            return

        df = self._create_dataframe(flights)
        Ingest.logger.info('Fetched %d flight records from FlightAware.' % df.count())

        self.save_dataset(df, self.FLIGHT_TABLE_NAME)
        Ingest.logger.info('FlightAware data ingestion complete.')

    def _get_api_key(self) -> str:
        """
        Retrieves the FlightAware API key from the aiSSEMBLE Configuration Store
        (backed by Krausening properties). The key should be stored in a properties
        file named 'flightaware.properties' with the property 'api.key'.

        Do NOT hardcode the API key. Use Sealed Secrets or the Configuration Store
        to manage secrets securely at runtime.
        """
        properties = PropertyManager.get_instance().get_properties(
            "flightaware.properties"
        )
        return properties.getProperty("api.key", "")

    def _fetch_flights(self, api_key: str) -> list:
        """
        Calls the FlightAware AeroAPI flights/search endpoint to retrieve
        current flight data. Returns a list of flight dictionaries.
        """
        url = f"{self.AEROAPI_BASE_URL}/flights/search"
        headers = {"x-apikey": api_key}
        params = {
            "query": "-belowAltitude 500 -aboveGroundspeed 0",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("flights", [])
        except requests.exceptions.HTTPError as http_err:
            Ingest.logger.error(
                'FlightAware API HTTP error: %s' % str(http_err)
            )
        except requests.exceptions.ConnectionError as conn_err:
            Ingest.logger.error(
                'FlightAware API connection error: %s' % str(conn_err)
            )
        except requests.exceptions.Timeout as timeout_err:
            Ingest.logger.error(
                'FlightAware API timeout error: %s' % str(timeout_err)
            )
        except requests.exceptions.RequestException as req_err:
            Ingest.logger.error(
                'FlightAware API request error: %s' % str(req_err)
            )

        return []

    def _create_dataframe(self, flights: list):
        """
        Converts a list of flight dictionaries from the FlightAware API response
        into a PySpark DataFrame with a well-defined schema.
        """
        ingestion_ts = datetime.now(timezone.utc).isoformat()
        rows = []

        for flight in flights:
            origin = flight.get("origin", {}) or {}
            destination = flight.get("destination", {}) or {}

            row = Row(
                ident=flight.get("ident"),
                ident_icao=flight.get("ident_icao"),
                ident_iata=flight.get("ident_iata"),
                fa_flight_id=flight.get("fa_flight_id"),
                operator=flight.get("operator"),
                operator_icao=flight.get("operator_icao"),
                operator_iata=flight.get("operator_iata"),
                flight_number=flight.get("flight_number"),
                registration=flight.get("registration"),
                atc_ident=flight.get("atc_ident"),
                inbound_fa_flight_id=flight.get("inbound_fa_flight_id"),
                codeshares=str(flight.get("codeshares")) if flight.get("codeshares") else None,
                codeshares_iata=str(flight.get("codeshares_iata")) if flight.get("codeshares_iata") else None,
                blocked=flight.get("blocked"),
                diverted=flight.get("diverted"),
                cancelled=flight.get("cancelled"),
                position_only=flight.get("position_only"),
                origin_code=origin.get("code"),
                origin_name=origin.get("name"),
                origin_city=origin.get("city"),
                destination_code=destination.get("code"),
                destination_name=destination.get("name"),
                destination_city=destination.get("city"),
                departure_time=flight.get("departure_time"),
                arrival_time=flight.get("arrival_time"),
                filed_ete=flight.get("filed_ete"),
                progress_percent=flight.get("progress_percent"),
                status=flight.get("status"),
                aircraft_type=flight.get("aircraft_type"),
                route_distance=flight.get("route_distance"),
                filed_airspeed=flight.get("filed_airspeed"),
                filed_altitude=flight.get("filed_altitude"),
                route=flight.get("route"),
                baggage_claim=flight.get("baggage_claim"),
                seats_cabin_business=flight.get("seats_cabin_business"),
                seats_cabin_coach=flight.get("seats_cabin_coach"),
                seats_cabin_first=flight.get("seats_cabin_first"),
                gate_origin=flight.get("gate_origin"),
                gate_destination=flight.get("gate_destination"),
                terminal_origin=flight.get("terminal_origin"),
                terminal_destination=flight.get("terminal_destination"),
                type=flight.get("type"),
                scheduled_out=flight.get("scheduled_out"),
                estimated_out=flight.get("estimated_out"),
                actual_out=flight.get("actual_out"),
                scheduled_off=flight.get("scheduled_off"),
                estimated_off=flight.get("estimated_off"),
                actual_off=flight.get("actual_off"),
                scheduled_on=flight.get("scheduled_on"),
                estimated_on=flight.get("estimated_on"),
                actual_on=flight.get("actual_on"),
                scheduled_in=flight.get("scheduled_in"),
                estimated_in=flight.get("estimated_in"),
                actual_in=flight.get("actual_in"),
                ingestion_timestamp=ingestion_ts,
            )
            rows.append(row)

        return self.spark.createDataFrame(rows, schema=self.FLIGHT_SCHEMA)
