import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from data_transform_core.data_transform_exception import (
    DataTransformException,
)


class TestDataTransformException:
    def test_inherits_from_exception(self):
        assert issubclass(DataTransformException, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(DataTransformException):
            raise DataTransformException("transform failed")

    def test_message_preserved(self):
        with pytest.raises(
            DataTransformException, match="specific error"
        ):
            raise DataTransformException("specific error")

    def test_empty_message(self):
        with pytest.raises(DataTransformException):
            raise DataTransformException()

    def test_is_instance_of_exception(self):
        exc = DataTransformException("test")
        assert isinstance(exc, Exception)
