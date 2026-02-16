import sys
import os
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from aissemble_core_metadata.metadata_model import MetadataModel


@pytest.fixture(autouse=True)
def mock_dependencies():
    mock_props = MagicMock()
    mock_pm = MagicMock()
    mock_pm.get_properties.return_value = mock_props
    mock_props.getProperty.return_value = "kafka:9093"

    with patch(
        "aissemble_core_config.messaging_config.PropertyManager"
    ) as mock_pm_class, patch(
        "aissemble_core_metadata.hive_metadata_api_service.KafkaProducer"
    ) as mock_kafka:
        mock_pm_class.get_instance.return_value = mock_pm
        mock_producer = MagicMock()
        mock_kafka.return_value = mock_producer
        yield {
            "producer": mock_producer,
            "props": mock_props,
        }


class TestHiveMetadataAPIService:
    def test_create_metadata_sends_to_kafka(self, mock_dependencies):
        from aissemble_core_metadata.hive_metadata_api_service import (
            HiveMetadataAPIService,
        )

        service = HiveMetadataAPIService()
        metadata = MetadataModel(
            resource="res-1",
            subject="sub-1",
            action="create",
        )
        service.create_metadata(metadata)
        mock_dependencies["producer"].send.assert_called_once()

    def test_create_metadata_with_none_does_not_send(self, mock_dependencies):
        from aissemble_core_metadata.hive_metadata_api_service import (
            HiveMetadataAPIService,
        )

        service = HiveMetadataAPIService()
        service.create_metadata(None)
        mock_dependencies["producer"].send.assert_not_called()

    def test_get_metadata_returns_empty_list(self, mock_dependencies):
        from aissemble_core_metadata.hive_metadata_api_service import (
            HiveMetadataAPIService,
        )

        service = HiveMetadataAPIService()
        result = service.get_metadata({"key": "value"})
        assert result == []

    def test_init_creates_kafka_producer(self, mock_dependencies):
        from aissemble_core_metadata.hive_metadata_api_service import (
            HiveMetadataAPIService,
        )

        service = HiveMetadataAPIService()
        assert service.producer is not None
