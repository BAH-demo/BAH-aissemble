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
        "aissemble_core_config.spark_neo4j_config.PropertyManager"
    ) as mock_class:
        mock_class.get_instance.return_value = mock_pm
        yield mock_props


class TestSparkNeo4jConfig:
    def test_url_returns_configured_value(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="bolt://custom:7687"
        )
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.url() == "bolt://custom:7687"

    def test_url_returns_default_when_none(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.url() == "bolt://neo4j:7687"

    def test_authentication_type_returns_configured_value(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="kerberos")
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.authentication_type() == "kerberos"

    def test_authentication_type_returns_default_when_none(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.authentication_type() == "basic"

    def test_authentication_basic_username_default(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.authentication_basic_username() == "neo4j"

    def test_authentication_basic_password_default(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.authentication_basic_password() == "p455w0rd"

    def test_authentication_kerberos_ticket_returns_none_when_not_set(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.authentication_kerberos_ticket() is None

    def test_encryption_enabled_returns_property(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value="true")
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.encryption_enabled() == "true"

    def test_connection_timeout_msecs_returns_property(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value="5000")
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        assert config.connection_timeout_msecs() == "5000"

    def test_get_spark_options_excludes_none_values(
        self, mock_property_manager
    ):
        def side_effect(key):
            if key == "url":
                return "bolt://host:7687"
            if key == "authentication.type":
                return "basic"
            if key == "authentication.basic.username":
                return "neo4j"
            if key == "authentication.basic.password":
                return "pass"
            return None

        mock_property_manager.__getitem__ = MagicMock(side_effect=side_effect)
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        options = config.get_spark_options()
        assert "url" in options
        assert "authentication.type" in options
        assert "authentication.kerberos.ticket" not in options
        assert "encryption.enabled" not in options

    def test_get_spark_options_includes_all_set_values(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="test-value"
        )
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        config = SparkNeo4jConfig()
        options = config.get_spark_options()
        assert len(options) == 15

    def test_neo4j_format_constant(self, mock_property_manager):
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        assert SparkNeo4jConfig.NEO4J_FORMAT == "org.neo4j.spark.DataSource"

    def test_labels_option_constant(self, mock_property_manager):
        from aissemble_core_config.spark_neo4j_config import SparkNeo4jConfig

        assert SparkNeo4jConfig.LABELS_OPTION == "labels"
