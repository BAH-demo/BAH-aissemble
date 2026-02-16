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


@pytest.fixture(autouse=True)
def mock_property_manager():
    mock_props = MagicMock()
    mock_pm = MagicMock()
    mock_pm.get_properties.return_value = mock_props
    with patch(
        "aissemble_core_config.messaging_config.PropertyManager"
    ) as mock_class:
        mock_class.get_instance.return_value = mock_pm
        yield mock_props


class TestMessagingConfig:
    def test_server_returns_configured_value(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "my-kafka:9092"
        from aissemble_core_config.messaging_config import MessagingConfig

        config = MessagingConfig()
        result = config.server()
        assert result == "my-kafka:9092"
        mock_property_manager.getProperty.assert_called_with(
            "server", "kafka-cluster:9093"
        )

    def test_server_returns_default_when_not_configured(
        self, mock_property_manager
    ):
        mock_property_manager.getProperty.return_value = "kafka-cluster:9093"
        from aissemble_core_config.messaging_config import MessagingConfig

        config = MessagingConfig()
        result = config.server()
        assert result == "kafka-cluster:9093"

    def test_metadata_topic_returns_configured_value(
        self, mock_property_manager
    ):
        mock_property_manager.getProperty.return_value = "custom-topic"
        from aissemble_core_config.messaging_config import MessagingConfig

        config = MessagingConfig()
        result = config.metadata_topic()
        assert result == "custom-topic"
        mock_property_manager.getProperty.assert_called_with(
            "metadata_topic", "metadata-ingest"
        )

    def test_metadata_topic_returns_default_when_not_configured(
        self, mock_property_manager
    ):
        mock_property_manager.getProperty.return_value = "metadata-ingest"
        from aissemble_core_config.messaging_config import MessagingConfig

        config = MessagingConfig()
        result = config.metadata_topic()
        assert result == "metadata-ingest"
