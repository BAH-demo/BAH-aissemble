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

from drift.detection.rest.client.drift_rest_client import (
    DriftData,
    DriftVariable,
    DriftVariables,
    DriftDataInput,
    DriftDetectionResult,
    DriftRestClient,
)


class TestDriftData:
    def test_default_name_is_none(self):
        data = DriftData()
        assert data.name is None

    def test_custom_name(self):
        data = DriftData(name="test-drift")
        assert data.name == "test-drift"


class TestDriftVariable:
    def test_create_drift_variable(self):
        var = DriftVariable(value=0.95)
        assert var.value == 0.95
        assert var.type == "single"
        assert var.name is None

    def test_drift_variable_with_name(self):
        var = DriftVariable(name="accuracy", value=0.87)
        assert var.name == "accuracy"
        assert var.value == 0.87

    def test_drift_variable_inherits_from_drift_data(self):
        assert issubclass(DriftVariable, DriftData)

    def test_drift_variable_negative_value(self):
        var = DriftVariable(value=-0.5)
        assert var.value == -0.5

    def test_drift_variable_zero_value(self):
        var = DriftVariable(value=0.0)
        assert var.value == 0.0


class TestDriftVariables:
    def test_default_variables_empty(self):
        vars_ = DriftVariables()
        assert vars_.variables == []
        assert vars_.type == "multiple"

    def test_with_variables(self):
        v1 = DriftVariable(name="v1", value=1.0)
        v2 = DriftVariable(name="v2", value=2.0)
        vars_ = DriftVariables(variables=[v1, v2])
        assert len(vars_.variables) == 2

    def test_inherits_from_drift_data(self):
        assert issubclass(DriftVariables, DriftData)

    def test_with_name(self):
        vars_ = DriftVariables(name="feature-group")
        assert vars_.name == "feature-group"


class TestDriftDataInput:
    def test_default_values(self):
        data_input = DriftDataInput()
        assert data_input.input is None
        assert data_input.control is None

    def test_with_single_variables(self):
        input_var = DriftVariable(name="input", value=0.5)
        control_var = DriftVariable(name="control", value=0.3)
        data_input = DriftDataInput(input=input_var, control=control_var)
        assert data_input.input.value == 0.5
        assert data_input.control.value == 0.3

    def test_with_multiple_variables(self):
        input_vars = DriftVariables(
            variables=[DriftVariable(value=1.0), DriftVariable(value=2.0)]
        )
        control_vars = DriftVariables(
            variables=[DriftVariable(value=1.1), DriftVariable(value=2.1)]
        )
        data_input = DriftDataInput(input=input_vars, control=control_vars)
        assert len(data_input.input.variables) == 2


class TestDriftDetectionResult:
    def test_create_result_with_drift(self):
        result = DriftDetectionResult(
            hasDrift=True,
            timestamp="2024-01-01T00:00:00",
            metadata={"algorithm": "kolmogorov-smirnov"},
        )
        assert result.hasDrift is True
        assert result.timestamp == "2024-01-01T00:00:00"
        assert result.metadata["algorithm"] == "kolmogorov-smirnov"

    def test_create_result_without_drift(self):
        result = DriftDetectionResult(
            hasDrift=False,
            timestamp="2024-06-15T12:00:00",
            metadata={},
        )
        assert result.hasDrift is False
        assert result.metadata == {}

    def test_result_with_rich_metadata(self):
        result = DriftDetectionResult(
            hasDrift=True,
            timestamp="t",
            metadata={
                "p_value": 0.01,
                "threshold": 0.05,
                "statistic": 0.35,
            },
        )
        assert result.metadata["p_value"] == 0.01


class TestDriftRestClient:
    @pytest.fixture(autouse=True)
    def mock_rest_config(self):
        with patch(
            "config.rest_config.PropertyManager"
        ) as mock_pm_class:
            mock_props = MagicMock()
            mock_pm = MagicMock()
            mock_pm.get_properties.return_value = mock_props
            mock_props.__getitem__ = MagicMock(
                return_value="http://drift-service:8084"
            )
            mock_pm_class.get_instance.return_value = mock_pm
            yield

    @patch("drift.detection.rest.client.drift_rest_client.requests")
    def test_invoke_drift_sends_post_request(self, mock_requests):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        client = DriftRestClient()
        input_var = DriftVariable(name="input", value=0.5)
        control_var = DriftVariable(name="control", value=0.3)

        result = client.invoke_drift("policy-1", input_var, control_var)

        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert "/invoke-drift" in call_args[0][0]
        assert call_args[1]["params"] == {"policyIdentifier": "policy-1"}
        assert result == mock_response

    @patch("drift.detection.rest.client.drift_rest_client.requests")
    def test_invoke_drift_with_none_inputs(self, mock_requests):
        mock_response = MagicMock()
        mock_requests.post.return_value = mock_response

        client = DriftRestClient()
        result = client.invoke_drift("policy-2", None, None)

        mock_requests.post.assert_called_once()
        assert result == mock_response

    @patch("drift.detection.rest.client.drift_rest_client.requests")
    def test_invoke_drift_uses_correct_headers(self, mock_requests):
        mock_requests.post.return_value = MagicMock()

        client = DriftRestClient()
        client.invoke_drift("p", DriftVariable(value=1.0), None)

        call_args = mock_requests.post.call_args
        assert call_args[1]["headers"] == {
            "Content-type": "application/json"
        }

    @patch("drift.detection.rest.client.drift_rest_client.requests")
    def test_invoke_drift_url_includes_hostname(self, mock_requests):
        mock_requests.post.return_value = MagicMock()

        client = DriftRestClient()
        client.invoke_drift("p", None, None)

        call_args = mock_requests.post.call_args
        assert call_args[0][0].startswith("http://drift-service:8084")
