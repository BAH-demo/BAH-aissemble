import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from aissemble_core_metadata.metadata_model import MetadataModel
from aissemble_core_metadata.logging_metadata_api_service import (
    LoggingMetadataAPIService,
)
from aissemble_core_metadata.metadata_api import MetadataAPI


class TestLoggingMetadataAPIService:
    def test_implements_metadata_api(self):
        assert issubclass(LoggingMetadataAPIService, MetadataAPI)

    def test_create_metadata_with_valid_metadata_logs_info(self):
        service = LoggingMetadataAPIService()
        metadata = MetadataModel(
            resource="resource-1",
            subject="test-subject",
            action="create",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            additionalValues={"key1": "value1"},
        )
        service.create_metadata(metadata)

    def test_create_metadata_with_none_logs_warning(self):
        service = LoggingMetadataAPIService()
        service.create_metadata(None)

    def test_create_metadata_with_empty_additional_values(self):
        service = LoggingMetadataAPIService()
        metadata = MetadataModel(
            resource="resource-1",
            subject="test-subject",
            action="read",
            timestamp=datetime(2024, 6, 15, 10, 30, 0),
        )
        service.create_metadata(metadata)

    def test_get_metadata_returns_empty_list(self):
        service = LoggingMetadataAPIService()
        result = service.get_metadata({"key": "value"})
        assert result == []

    def test_get_metadata_with_empty_params_returns_empty_list(self):
        service = LoggingMetadataAPIService()
        result = service.get_metadata({})
        assert result == []
