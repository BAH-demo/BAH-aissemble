from unittest.mock import MagicMock

import pytest

from aissemble_messaging.message import Message
from aissemble_messaging.transfer.callback import Callback
from aissemble_messaging.exception.process_message_error import (
    ProcessMessageError,
)


class TestCallback:
    def test_init_stores_process_callable(self):
        def my_process(msg):
            pass

        callback = Callback(my_process)
        assert callback.process == my_process

    def test_execute_calls_process_with_message(self):
        mock_process = MagicMock(return_value="processed")
        callback = Callback(mock_process)
        mock_handle = MagicMock()

        result = callback.execute(mock_handle)

        mock_process.assert_called_once()
        call_arg = mock_process.call_args[0][0]
        assert isinstance(call_arg, Message)
        assert result == "processed"

    def test_execute_raises_process_message_error_on_exception(self):
        def failing_process(msg):
            raise ValueError("bad data")

        callback = Callback(failing_process)
        mock_handle = MagicMock()

        with pytest.raises(ProcessMessageError):
            callback.execute(mock_handle)

    def test_create_message_returns_message_with_handle(self):
        callback = Callback(lambda msg: None)
        mock_handle = MagicMock()
        msg = callback._create_message(mock_handle)
        assert isinstance(msg, Message)
        assert msg.message_handle == mock_handle

    def test_execute_with_lambda(self):
        callback = Callback(lambda msg: msg.get_payload())
        mock_handle = MagicMock()
        mock_handle.getPayload.return_value = "test-data"

        result = callback.execute(mock_handle)
        assert result == "test-data"

    def test_java_interface_declaration(self):
        assert hasattr(Callback, "Java")
        assert Callback.Java.implements == [
            "com.boozallen.aissemble.messaging.python.transfer.Callback"
        ]
