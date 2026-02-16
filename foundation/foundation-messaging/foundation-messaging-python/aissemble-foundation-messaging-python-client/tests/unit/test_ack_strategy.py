import pytest

from aissemble_messaging.ack_strategy import AckStrategy


class TestAckStrategy:
    def test_postprocessing_value(self):
        assert AckStrategy.POSTPROCESSING.value == 0

    def test_manual_value(self):
        assert AckStrategy.MANUAL.value == 1

    def test_enum_members(self):
        assert len(AckStrategy) == 2

    def test_from_value(self):
        assert AckStrategy(0) == AckStrategy.POSTPROCESSING
        assert AckStrategy(1) == AckStrategy.MANUAL

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            AckStrategy(99)
