from unittest.mock import MagicMock

from aissemble_messaging.message import Message


class TestMessage:
    def test_init_with_no_handle(self):
        msg = Message()
        assert msg.message_handle is None
        assert msg.content is None

    def test_init_with_message_handle(self):
        mock_handle = MagicMock()
        msg = Message(message_handle=mock_handle)
        assert msg.message_handle == mock_handle

    def test_get_payload_returns_content_when_no_handle(self):
        msg = Message()
        msg.set_payload("test-payload")
        assert msg.get_payload() == "test-payload"

    def test_get_payload_calls_handle_when_handle_present(self):
        mock_handle = MagicMock()
        mock_handle.getPayload.return_value = "java-payload"
        msg = Message(message_handle=mock_handle)
        result = msg.get_payload()
        assert result == "java-payload"
        mock_handle.getPayload.assert_called_once()

    def test_set_payload(self):
        msg = Message()
        msg.set_payload("my-content")
        assert msg.content == "my-content"

    def test_set_payload_overwrites_previous(self):
        msg = Message()
        msg.set_payload("first")
        msg.set_payload("second")
        assert msg.content == "second"

    def test_ack_delegates_to_handle(self):
        mock_handle = MagicMock()
        mock_handle.ack.return_value = "ack-result"
        msg = Message(message_handle=mock_handle)
        result = msg.ack()
        assert result == "ack-result"
        mock_handle.ack.assert_called_once()

    def test_nack_delegates_to_handle(self):
        mock_handle = MagicMock()
        mock_handle.nack.return_value = "nack-result"
        msg = Message(message_handle=mock_handle)
        result = msg.nack("error occurred")
        assert result == "nack-result"
        mock_handle.nack.assert_called_once_with("error occurred")

    def test_get_payload_with_none_content_and_no_handle(self):
        msg = Message()
        assert msg.get_payload() is None

    def test_set_payload_empty_string(self):
        msg = Message()
        msg.set_payload("")
        assert msg.get_payload() == ""
