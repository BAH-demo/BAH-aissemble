import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from inference.inference_request import InferenceRequest
from inference.inference_result import InferenceResult
from inference.inference_request_batch import InferenceRequestBatch
from inference.inference_result_batch import InferenceResultBatch


class TestInferenceRequest:
    def test_default_values(self):
        req = InferenceRequest()
        assert req.source_ip_address == ""
        assert req.created == 0
        assert req.kind == ""
        assert req.category == ""
        assert req.outcome == ""

    def test_custom_values(self):
        req = InferenceRequest(
            source_ip_address="192.168.1.1",
            created=1234567890,
            kind="network",
            category="intrusion",
            outcome="blocked",
        )
        assert req.source_ip_address == "192.168.1.1"
        assert req.created == 1234567890
        assert req.kind == "network"
        assert req.category == "intrusion"
        assert req.outcome == "blocked"

    def test_setters(self):
        req = InferenceRequest()
        req.source_ip_address = "10.0.0.1"
        req.created = 999
        req.kind = "malware"
        req.category = "trojan"
        req.outcome = "detected"

        assert req.source_ip_address == "10.0.0.1"
        assert req.created == 999
        assert req.kind == "malware"
        assert req.category == "trojan"
        assert req.outcome == "detected"


class TestInferenceResult:
    def test_default_values(self):
        result = InferenceResult()
        assert result.threat_detected is False
        assert result.score == 0

    def test_custom_values(self):
        result = InferenceResult(threat_detected=True, score=95)
        assert result.threat_detected is True
        assert result.score == 95

    def test_setters(self):
        result = InferenceResult()
        result.threat_detected = True
        result.score = 50
        assert result.threat_detected is True
        assert result.score == 50


class TestInferenceRequestBatch:
    def test_create_batch(self):
        requests = [
            InferenceRequest(source_ip_address="1.1.1.1"),
            InferenceRequest(source_ip_address="2.2.2.2"),
        ]
        batch = InferenceRequestBatch(row_id_key="id", data=requests)
        assert batch.row_id_key == "id"
        assert len(batch.data) == 2

    def test_setters(self):
        batch = InferenceRequestBatch(row_id_key="old_key", data=[])
        batch.row_id_key = "new_key"
        batch.data = [InferenceRequest()]
        assert batch.row_id_key == "new_key"
        assert len(batch.data) == 1

    def test_empty_batch(self):
        batch = InferenceRequestBatch(row_id_key="key", data=[])
        assert batch.data == []


class TestInferenceResultBatch:
    def test_create_result_batch(self):
        result = InferenceResult(threat_detected=True, score=80)
        batch = InferenceResultBatch(row_id_key="row-1", result=result)
        assert batch.row_id_key == "row-1"
        assert batch.result.threat_detected is True
        assert batch.result.score == 80

    def test_setters(self):
        result1 = InferenceResult(score=10)
        result2 = InferenceResult(score=20)
        batch = InferenceResultBatch(row_id_key="r1", result=result1)
        batch.result = result2
        batch.row_id_key = "r2"
        assert batch.row_id_key == "r2"
        assert batch.result.score == 20


class TestInferenceConfig:
    @pytest.fixture(autouse=True)
    def mock_property_manager(self):
        mock_props = MagicMock()
        mock_pm = MagicMock()
        mock_pm.get_properties.return_value = mock_props
        with patch(
            "inference.inference_config.PropertyManager"
        ) as mock_class:
            mock_class.get_instance.return_value = mock_pm
            yield mock_props

    def test_rest_service_url_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "http://localhost"
        from inference.inference_config import InferenceConfig

        config = InferenceConfig()
        assert config.rest_service_url() == "http://localhost"

    def test_rest_service_url_custom(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "http://inference-svc"
        from inference.inference_config import InferenceConfig

        config = InferenceConfig()
        assert config.rest_service_url() == "http://inference-svc"

    def test_rest_service_port_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "7080"
        from inference.inference_config import InferenceConfig

        config = InferenceConfig()
        assert config.rest_service_port() == "7080"

    def test_grpc_service_url_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "http://localhost"
        from inference.inference_config import InferenceConfig

        config = InferenceConfig()
        assert config.grpc_service_url() == "http://localhost"

    def test_grpc_service_port_default(self, mock_property_manager):
        mock_property_manager.getProperty.return_value = "7081"
        from inference.inference_config import InferenceConfig

        config = InferenceConfig()
        assert config.grpc_service_port() == "7081"


class TestRestInferenceClient:
    @pytest.fixture(autouse=True)
    def mock_inference_config(self):
        with patch(
            "inference.inference_config.PropertyManager"
        ) as mock_class:
            mock_props = MagicMock()
            mock_pm = MagicMock()
            mock_pm.get_properties.return_value = mock_props
            mock_props.getProperty.side_effect = lambda key, default="": default
            mock_class.get_instance.return_value = mock_pm
            yield

    @pytest.mark.asyncio
    async def test_infer_calls_make_request(self):
        from inference.rest_inference_client import RestInferenceClient

        client = RestInferenceClient()
        mock_response = {"threat_detected": True, "score": 85}

        with patch.object(
            client,
            "_RestInferenceClient__make_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            req = InferenceRequest(source_ip_address="1.1.1.1")
            result = await client.infer(req)
            assert result.threat_detected is True
            assert result.score == 85

    @pytest.mark.asyncio
    async def test_infer_batch_calls_make_request(self):
        from inference.rest_inference_client import RestInferenceClient

        client = RestInferenceClient()
        mock_response = {
            "results": [
                {
                    "row_id": "r1",
                    "result": {"threat_detected": False, "score": 10},
                }
            ]
        }

        with patch.object(
            client,
            "_RestInferenceClient__make_request",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            batch = InferenceRequestBatch(
                row_id_key="id", data=[InferenceRequest()]
            )
            results = await client.infer_batch(batch)
            assert len(results) == 1
            assert results[0].row_id_key == "r1"
