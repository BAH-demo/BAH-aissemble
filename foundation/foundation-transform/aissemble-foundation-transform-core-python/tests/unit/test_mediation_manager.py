import sys
import os
from unittest.mock import MagicMock, patch
from typing import Dict

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from data_transform_core.mediator.mediation_objects import (
    MediationContext,
    MediationConfiguration,
    MediationProperty,
    MediationException,
)
from data_transform_core.mediator.mediator import Mediator
from data_transform_core.mediator.pass_through_mediator import (
    PassThroughMediator,
)
from data_transform_core.mediator.mediation_manager import MediationManager


class StubMediator(Mediator):
    def performMediation(self, input, properties: Dict[str, str]):
        return f"stub:{input}"


class TestMediationManager:
    def test_init_empty_maps(self):
        mm = MediationManager()
        assert mm._mediationOptionMap == {}
        assert mm._mediationPropertyMap == {}

    def test_get_mediator_returns_pass_through_when_not_found(self):
        mm = MediationManager()
        ctx = MediationContext(inputType="a", outputType="b")
        mediator = mm.getMediator(ctx)
        assert isinstance(mediator, PassThroughMediator)

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_validate_and_add_mediator_adds_valid_mediator(
        self, mock_import
    ):
        mock_module = MagicMock()
        mock_module.StubMediator = StubMediator
        mock_import.return_value = mock_module

        mm = MediationManager()
        config = MediationConfiguration(
            inputType="json",
            outputType="csv",
            className="my_module.StubMediator",
        )
        mm.validateAndAddMediator([config], config)

        ctx = MediationContext(inputType="json", outputType="csv")
        mediator = mm.getMediator(ctx)
        assert isinstance(mediator, StubMediator)

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_validate_and_add_mediator_rejects_non_mediator_class(
        self, mock_import
    ):
        mock_module = MagicMock()
        mock_module.NotAMediator = str
        mock_import.return_value = mock_module

        mm = MediationManager()
        config = MediationConfiguration(
            inputType="x",
            outputType="y",
            className="my_module.NotAMediator",
        )
        mm.validateAndAddMediator([config], config)

        ctx = MediationContext(inputType="x", outputType="y")
        mediator = mm.getMediator(ctx)
        assert isinstance(mediator, PassThroughMediator)

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_validate_and_add_mediator_handles_import_error(
        self, mock_import
    ):
        mock_import.side_effect = ModuleNotFoundError("no module")

        mm = MediationManager()
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="nonexistent.Module",
        )
        mm.validateAndAddMediator([config], config)

        ctx = MediationContext(inputType="a", outputType="b")
        mediator = mm.getMediator(ctx)
        assert isinstance(mediator, PassThroughMediator)

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_add_mediator_properties(self, mock_import):
        mock_module = MagicMock()
        mock_module.StubMediator = StubMediator
        mock_import.return_value = mock_module

        mm = MediationManager()
        props = [
            MediationProperty(key="delimiter", value=","),
            MediationProperty(key="encoding", value="utf-8"),
        ]
        config = MediationConfiguration(
            inputType="json",
            outputType="csv",
            className="my_module.StubMediator",
            properties=props,
        )
        mm.validateAndAddMediator([config], config)

        ctx = MediationContext(inputType="json", outputType="csv")
        mediator = mm.getMediator(ctx)
        assert mediator.properties == {
            "delimiter": ",",
            "encoding": "utf-8",
        }

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_add_mediator_no_properties(self, mock_import):
        mock_module = MagicMock()
        mock_module.StubMediator = StubMediator
        mock_import.return_value = mock_module

        mm = MediationManager()
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="my_module.StubMediator",
        )
        mm.validateAndAddMediator([config], config)

        ctx = MediationContext(inputType="a", outputType="b")
        mediator = mm.getMediator(ctx)
        assert mediator.properties is None

    @patch("data_transform_core.mediator.mediation_manager.import_module")
    def test_duplicate_mediation_definitions_overwrites(self, mock_import):
        mock_module = MagicMock()
        mock_module.StubMediator = StubMediator
        mock_import.return_value = mock_module

        mm = MediationManager()
        config1 = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="my_module.StubMediator",
        )
        config2 = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="my_module.StubMediator",
        )
        mm.validateAndAddMediator([config1], config1)
        mm.validateAndAddMediator([config2], config2)

        ctx = MediationContext(inputType="a", outputType="b")
        mediator = mm.getMediator(ctx)
        assert isinstance(mediator, StubMediator)
