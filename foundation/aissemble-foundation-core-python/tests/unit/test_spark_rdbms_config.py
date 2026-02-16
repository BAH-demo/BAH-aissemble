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
        "aissemble_core_config.spark_rdbms_config.PropertyManager"
    ) as mock_class:
        mock_class.get_instance.return_value = mock_pm
        yield mock_props


class TestSparkRDBMSConfig:
    def test_jdbc_url_returns_configured_value(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = (
            "jdbc:postgresql://custom:5432/mydb"
        )
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        assert config.jdbc_url() == "jdbc:postgresql://custom:5432/mydb"

    def test_jdbc_url_returns_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = (
            "jdbc:postgresql://postgres:5432/db"
        )
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        result = config.jdbc_url()
        assert result == "jdbc:postgresql://postgres:5432/db"
        mock_property_manager.getProperty.assert_called_with(
            "jdbc.url", "jdbc:postgresql://postgres:5432/db"
        )

    def test_jdbc_driver_returns_configured_value(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "com.mysql.cj.jdbc.Driver"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        assert config.jdbc_driver() == "com.mysql.cj.jdbc.Driver"

    def test_jdbc_driver_returns_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "org.postgresql.Driver"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        result = config.jdbc_driver()
        assert result == "org.postgresql.Driver"
        mock_property_manager.getProperty.assert_called_with(
            "jdbc.driver", "org.postgresql.Driver"
        )

    def test_user_returns_configured_value(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "admin"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        assert config.user() == "admin"

    def test_user_returns_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "postgres"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        result = config.user()
        assert result == "postgres"
        mock_property_manager.getProperty.assert_called_with(
            "jdbc.user", "postgres"
        )

    def test_password_returns_configured_value(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "s3cret"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        assert config.password() == "s3cret"

    def test_password_returns_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "password"
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        config = SparkRDBMSConfig()
        result = config.password()
        assert result == "password"
        mock_property_manager.getProperty.assert_called_with(
            "jdbc.password", "password"
        )

    def test_default_constants(self, mock_property_manager):
        from aissemble_core_config.spark_rdbms_config import SparkRDBMSConfig

        assert (
            SparkRDBMSConfig.DEFAULT_JDBC_URL
            == "jdbc:postgresql://postgres:5432/db"
        )
        assert SparkRDBMSConfig.DEFAULT_JDBC_DRIVER == "org.postgresql.Driver"
        assert SparkRDBMSConfig.DEFAULT_USER == "postgres"
        assert SparkRDBMSConfig.DEFAULT_PASSWORD == "password"
