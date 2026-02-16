import uuid

from aissemble_messaging.future import Future


class TestFuture:
    def test_init_stores_service_future(self):
        mock_obj = "mock-service-future"
        future = Future(mock_obj)
        assert future.serviceFuture == "mock-service-future"

    def test_init_generates_uuid(self):
        future = Future("obj")
        assert future.futureId is not None
        assert isinstance(future.futureId, uuid.UUID)

    def test_each_future_gets_unique_id(self):
        f1 = Future("obj1")
        f2 = Future("obj2")
        assert f1.futureId != f2.futureId

    def test_get_result_returns_none(self):
        future = Future("obj")
        result = future.getResult()
        assert result is None
