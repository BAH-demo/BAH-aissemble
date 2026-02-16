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

from aissemble_core_filestore.file_store_factory import FileStoreFactory


class TestFileStoreFactory:
    def test_create_local_file_store(self):
        mock_cls = MagicMock()
        mock_driver = MagicMock()
        mock_cls.return_value = mock_driver
        filtered = {"test_FS_ACCESS_KEY_ID": "/tmp/local-store"}

        result = FileStoreFactory.create_local_file_store(
            "test", filtered, mock_cls
        )

        mock_cls.assert_called_once_with("/tmp/local-store")
        assert result == mock_driver

    @patch("aissemble_core_filestore.file_store_factory.get_driver")
    def test_create_s3_file_store_with_minimal_config(self, mock_get_driver):
        mock_cls = MagicMock()
        mock_driver = MagicMock()
        mock_cls.return_value = mock_driver
        mock_get_driver.return_value = mock_cls

        filtered = {
            "test_FS_ACCESS_KEY_ID": "my-access-key",
            "test_FS_SECRET_ACCESS_KEY": "my-secret-key",
        }

        result = FileStoreFactory.create_s3_file_store(
            "test", filtered, "s3"
        )

        mock_cls.assert_called_once_with(
            "my-access-key", "my-secret-key", True, None, None, None, None
        )
        assert result == mock_driver

    @patch("aissemble_core_filestore.file_store_factory.get_driver")
    def test_create_s3_file_store_with_all_options(self, mock_get_driver):
        mock_cls = MagicMock()
        mock_driver = MagicMock()
        mock_cls.return_value = mock_driver
        mock_get_driver.return_value = mock_cls

        filtered = {
            "test_FS_ACCESS_KEY_ID": "my-access-key",
            "test_FS_SECRET_ACCESS_KEY": "my-secret-key",
            "test_FS_SECURE": "false",
            "test_FS_HOST": "minio.local",
            "test_FS_PORT": "9000",
            "test_FS_API_VERSION": "v4",
            "test_FS_REGION": "us-east-1",
        }

        result = FileStoreFactory.create_s3_file_store(
            "test", filtered, "s3"
        )

        mock_cls.assert_called_once_with(
            "my-access-key",
            "my-secret-key",
            0,
            "minio.local",
            9000,
            "v4",
            "us-east-1",
        )
        assert result == mock_driver

    @patch("aissemble_core_filestore.file_store_factory.get_driver")
    def test_create_file_store_local_provider(self, mock_get_driver):
        mock_cls = MagicMock()
        mock_driver = MagicMock()
        mock_cls.return_value = mock_driver
        mock_get_driver.return_value = mock_cls

        env_vars = {
            "mystore_FS_PROVIDER": "local",
            "mystore_FS_ACCESS_KEY_ID": "/tmp/store",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            from libcloud.storage.types import Provider

            with patch(
                "aissemble_core_filestore.file_store_factory.Provider"
            ) as mock_provider:
                mock_provider.LOCAL = "local"
                mock_provider.S3 = "s3"
                result = FileStoreFactory.create_file_store("mystore")

        assert result == mock_driver

    @patch("aissemble_core_filestore.file_store_factory.get_driver")
    def test_create_file_store_unsupported_provider_returns_none(
        self, mock_get_driver
    ):
        mock_cls = MagicMock()
        mock_get_driver.return_value = mock_cls

        env_vars = {
            "mystore_FS_PROVIDER": "azure_blobs",
            "mystore_FS_ACCESS_KEY_ID": "key",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            with patch(
                "aissemble_core_filestore.file_store_factory.Provider"
            ) as mock_provider:
                mock_provider.LOCAL = "local"
                mock_provider.S3 = "s3"
                result = FileStoreFactory.create_file_store("mystore")

        assert result is None

    def test_create_file_store_missing_provider_raises_key_error(self):
        env_vars = {"mystore_OTHER": "value"}
        with patch.dict(os.environ, env_vars, clear=False):
            with pytest.raises(KeyError):
                FileStoreFactory.create_file_store("mystore")
