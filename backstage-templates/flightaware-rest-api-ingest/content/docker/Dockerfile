###############################################################################
# FlightAware REST API Ingest Pipeline – Container Image
#
# Built on the aiSSEMBLE PySpark base image.  Installs the pipeline
# dependencies and copies the ingest source code.
###############################################################################
ARG DOCKER_BASELINE_REPO_ID
ARG VERSION_AISSEMBLE

FROM ${DOCKER_BASELINE_REPO_ID}aissemble-spark-py:${VERSION_AISSEMBLE}

USER root

# -- Install Python dependencies --------------------------------------------
COPY pipelines/src/main/python/requirements.txt /opt/pipeline/requirements.txt
RUN pip install --no-cache-dir -r /opt/pipeline/requirements.txt

# -- Copy pipeline source code ----------------------------------------------
COPY pipelines/src/main/python/ /opt/pipeline/

# -- Environment defaults (override at runtime) -----------------------------
ENV FLIGHTAWARE_API_KEY="" \
    FLIGHTAWARE_BASE_URL="${{ values.flightawareApiBaseUrl }}" \
    FLIGHTAWARE_ENDPOINT="${{ values.flightawareApiEndpoint }}" \
    POLLING_INTERVAL_SECONDS="${{ values.pollingIntervalSeconds }}"

USER aissemble
WORKDIR /opt/pipeline

ENTRYPOINT ["python", "-m", "flightaware_ingest"]
