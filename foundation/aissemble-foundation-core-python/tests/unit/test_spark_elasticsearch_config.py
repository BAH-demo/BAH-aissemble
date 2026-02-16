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
        "aissemble_core_config.spark_elasticsearch_config.PropertyManager"
    ) as mock_class:
        mock_class.get_instance.return_value = mock_pm
        yield mock_props


class TestSparkElasticsearchConfig:
    def test_spark_es_nodes_returns_value_when_set(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(
            return_value="es-host-1,es-host-2"
        )
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.spark_es_nodes()
        assert result == "es-host-1,es-host-2"

    def test_spark_es_nodes_returns_default_when_none(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.spark_es_nodes()
        assert result == "localhost"

    def test_spark_es_port_returns_value_when_set(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value="9300")
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.spark_es_port()
        assert result == "9300"

    def test_spark_es_port_returns_default_when_none(
        self, mock_property_manager
    ):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.spark_es_port()
        assert result == "9200"

    def test_es_nodes_path_prefix_returns_property(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value="/prefix")
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.es_nodes_path_prefix()
        assert result == "/prefix"

    def test_es_nodes_discovery_returns_property(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value="true")
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        result = config.es_nodes_discovery()
        assert result == "true"

    def test_get_es_configs_includes_required_keys(self, mock_property_manager):
        mock_property_manager.__getitem__ = MagicMock(return_value=None)
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        configs = config.get_es_configs()
        assert "es.nodes" in configs
        assert "es.port" in configs
        assert configs["es.nodes"] == "localhost"
        assert configs["es.port"] == "9200"

    def test_get_es_configs_excludes_none_optional_values(
        self, mock_property_manager
    ):
        def side_effect(key):
            if key == "spark.es.nodes":
                return "myhost"
            if key == "spark.es.port":
                return "9200"
            return None

        mock_property_manager.__getitem__ = MagicMock(side_effect=side_effect)
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        configs = config.get_es_configs()
        assert "es.nodes" in configs
        assert "es.port" in configs
        assert "es.nodes.path.prefix" not in configs
        assert "es.nodes.discovery" not in configs

    def test_get_es_configs_includes_optional_values_when_set(
        self, mock_property_manager
    ):
        def side_effect(key):
            mapping = {
                "spark.es.nodes": "myhost",
                "spark.es.port": "9200",
                "es.nodes.path.prefix": "/my-prefix",
                "es.nodes.discovery": "false",
                "es.nodes.client.only": None,
                "es.nodes.data.only": None,
                "es.nodes.ingest.only": None,
                "es.nodes.wan.only": None,
                "es.http.timeout": "5m",
                "es.http.retries": "3",
                "es.net.http.auth.user": "admin",
                "es.net.http.auth.pass": "secret",
            }
            return mapping.get(key)

        mock_property_manager.__getitem__ = MagicMock(side_effect=side_effect)
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        configs = config.get_es_configs()
        assert configs["es.nodes.path.prefix"] == "/my-prefix"
        assert configs["es.nodes.discovery"] == "false"
        assert configs["es.http.timeout"] == "5m"
        assert configs["es.http.retries"] == "3"
        assert configs["es.net.http.auth.user"] == "admin"
        assert configs["es.net.http.auth.pass"] == "secret"

    def test_add_optional_config_adds_when_value_present(
        self, mock_property_manager
    ):
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        configs = {}
        config.add_optional_config(configs, "test.key", "test.value")
        assert configs["test.key"] == "test.value"

    def test_add_optional_config_skips_when_value_none(
        self, mock_property_manager
    ):
        from aissemble_core_config.spark_elasticsearch_config import (
            SparkElasticsearchConfig,
        )

        config = SparkElasticsearchConfig()
        configs = {}
        config.add_optional_config(configs, "test.key", None)
        assert "test.key" not in configs
