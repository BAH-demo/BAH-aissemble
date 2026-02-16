import pytest

from aissemble_messaging.exception.base_messaging_error import (
    BaseMessagingError,
)
from aissemble_messaging.exception.topic_not_supported_error import (
    TopicNotSupportedError,
)
from aissemble_messaging.exception.process_message_error import (
    ProcessMessageError,
)


class TestBaseMessagingError:
    def test_inherits_from_exception(self):
        assert issubclass(BaseMessagingError, Exception)

    def test_has_message_attribute(self):
        error = BaseMessagingError()
        error.message = "test error"
        assert error.message == "test error"


class TestTopicNotSupportedError:
    def test_inherits_from_base_error(self):
        assert issubclass(TopicNotSupportedError, BaseMessagingError)

    def test_stores_topic(self):
        error = TopicNotSupportedError("my-topic")
        assert error.topic == "my-topic"

    def test_message_includes_topic_name(self):
        error = TopicNotSupportedError("test-topic")
        assert "test-topic" in error.message

    def test_message_format(self):
        error = TopicNotSupportedError("orders")
        assert error.message == (
            "Could not find a topic to subscribe to named orders"
        )

    def test_is_exception(self):
        error = TopicNotSupportedError("t")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(TopicNotSupportedError) as exc_info:
            raise TopicNotSupportedError("missing-topic")
        assert exc_info.value.topic == "missing-topic"


class TestProcessMessageError:
    def test_inherits_from_base_error(self):
        assert issubclass(ProcessMessageError, BaseMessagingError)

    def test_stores_error_message(self):
        error = ProcessMessageError("failed to process")
        assert error.message == "failed to process"

    def test_empty_message(self):
        error = ProcessMessageError("")
        assert error.message == ""

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ProcessMessageError) as exc_info:
            raise ProcessMessageError("processing error")
        assert exc_info.value.message == "processing error"
