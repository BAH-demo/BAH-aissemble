import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from aissemble_core_metadata.metadata_model import MetadataModel


class TestMetadataModel:
    def test_create_metadata_model_with_defaults(self):
        model = MetadataModel()
        assert model.resource is not None
        assert model.subject == ""
        assert model.action == ""
        assert model.additionalValues == {}

    def test_create_metadata_model_with_values(self):
        model = MetadataModel(
            resource="res-123",
            subject="user-1",
            action="read",
            additionalValues={"key1": "value1"},
        )
        assert model.resource == "res-123"
        assert model.subject == "user-1"
        assert model.action == "read"
        assert model.additionalValues == {"key1": "value1"}

    def test_metadata_model_additional_values_multiple_entries(self):
        model = MetadataModel(
            additionalValues={"k1": "v1", "k2": "v2", "k3": "v3"}
        )
        assert len(model.additionalValues) == 3
        assert model.additionalValues["k2"] == "v2"

    def test_metadata_model_empty_strings(self):
        model = MetadataModel(
            resource="",
            subject="",
            action="",
        )
        assert model.resource == ""
        assert model.subject == ""
        assert model.action == ""

    def test_metadata_model_subject_and_action_set(self):
        model = MetadataModel(subject="pipeline-step", action="transform")
        assert model.subject == "pipeline-step"
        assert model.action == "transform"

    def test_metadata_model_is_pydantic_basemodel(self):
        from pydantic import BaseModel

        assert issubclass(MetadataModel, BaseModel)

    def test_metadata_model_dict_serialization(self):
        model = MetadataModel(
            resource="r1",
            subject="s1",
            action="a1",
        )
        data = model.model_dump()
        assert "resource" in data
        assert "subject" in data
        assert "action" in data
        assert "timestamp" in data
        assert "additionalValues" in data
