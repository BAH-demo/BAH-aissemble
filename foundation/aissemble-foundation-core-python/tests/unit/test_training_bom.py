import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from aissemble_core_bom.training_bom import TrainingBOM


class TestTrainingBOM:
    def test_create_training_bom(self):
        bom = TrainingBOM(
            id="bom-1",
            start_time="2024-01-01T00:00:00",
            end_time="2024-01-01T01:00:00",
            dataset_info=TrainingBOM.DatasetInfo(origin="s3://bucket/data"),
            feature_info=TrainingBOM.FeatureInfo(),
            model_info=TrainingBOM.ModelInfo(
                type="classification", architecture="resnet"
            ),
            mlflow_params={"lr": "0.01"},
            mlflow_metrics={"accuracy": "0.95"},
        )
        assert bom.id == "bom-1"
        assert bom.start_time == "2024-01-01T00:00:00"
        assert bom.end_time == "2024-01-01T01:00:00"

    def test_dataset_info_defaults(self):
        info = TrainingBOM.DatasetInfo(origin="local://data")
        assert info.origin == "local://data"
        assert info.size == 0

    def test_dataset_info_with_size(self):
        info = TrainingBOM.DatasetInfo(origin="s3://bucket", size=1000)
        assert info.size == 1000

    def test_feature_info_defaults(self):
        info = TrainingBOM.FeatureInfo()
        assert info.original_features == []
        assert info.selected_features == []

    def test_feature_info_with_features(self):
        info = TrainingBOM.FeatureInfo(
            original_features=["f1", "f2", "f3"],
            selected_features=["f1", "f3"],
        )
        assert len(info.original_features) == 3
        assert len(info.selected_features) == 2

    def test_model_info(self):
        info = TrainingBOM.ModelInfo(
            type="regression", architecture="linear"
        )
        assert info.type == "regression"
        assert info.architecture == "linear"

    def test_training_bom_mlflow_params(self):
        bom = TrainingBOM(
            id="bom-2",
            start_time="t0",
            end_time="t1",
            dataset_info=TrainingBOM.DatasetInfo(origin="origin"),
            feature_info=TrainingBOM.FeatureInfo(),
            model_info=TrainingBOM.ModelInfo(type="t", architecture="a"),
            mlflow_params={"param1": "v1", "param2": "v2"},
            mlflow_metrics={},
        )
        assert len(bom.mlflow_params) == 2
        assert bom.mlflow_metrics == {}

    def test_training_bom_serialization(self):
        bom = TrainingBOM(
            id="bom-3",
            start_time="t0",
            end_time="t1",
            dataset_info=TrainingBOM.DatasetInfo(origin="origin", size=500),
            feature_info=TrainingBOM.FeatureInfo(
                original_features=["a"], selected_features=["a"]
            ),
            model_info=TrainingBOM.ModelInfo(type="t", architecture="a"),
            mlflow_params={},
            mlflow_metrics={"loss": "0.1"},
        )
        data = bom.model_dump()
        assert data["id"] == "bom-3"
        assert data["dataset_info"]["size"] == 500
        assert data["mlflow_metrics"]["loss"] == "0.1"

    def test_training_bom_is_pydantic_model(self):
        from pydantic import BaseModel

        assert issubclass(TrainingBOM, BaseModel)
        assert issubclass(TrainingBOM.DatasetInfo, BaseModel)
        assert issubclass(TrainingBOM.FeatureInfo, BaseModel)
        assert issubclass(TrainingBOM.ModelInfo, BaseModel)
