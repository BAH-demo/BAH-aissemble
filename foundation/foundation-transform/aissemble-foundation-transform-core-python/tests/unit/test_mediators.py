import sys
import os
from typing import Dict

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from data_transform_core.mediator.mediator import Mediator
from data_transform_core.mediator.pass_through_mediator import (
    PassThroughMediator,
)
from data_transform_core.mediator.logging_mediator import LoggingMediator
from data_transform_core.mediator.mediation_objects import MediationException


class ConcreteMediator(Mediator):
    def performMediation(self, input, properties: Dict[str, str]):
        return f"mediated:{input}"


class FailingMediator(Mediator):
    def performMediation(self, input, properties: Dict[str, str]):
        raise ValueError("mediation failed")


class TestMediator:
    def test_mediator_is_abstract(self):
        with pytest.raises(TypeError):
            Mediator()

    def test_concrete_mediator_mediate(self):
        m = ConcreteMediator()
        result = m.mediate("hello")
        assert result == "mediated:hello"

    def test_properties_default_to_none(self):
        m = ConcreteMediator()
        assert m.properties is None

    def test_properties_setter(self):
        m = ConcreteMediator()
        m.properties = {"key": "value"}
        assert m.properties == {"key": "value"}

    def test_mediate_raises_mediation_exception_on_error(self):
        m = FailingMediator()
        with pytest.raises(MediationException):
            m.mediate("input")

    def test_mediate_with_none_input(self):
        m = ConcreteMediator()
        result = m.mediate(None)
        assert result == "mediated:None"


class TestPassThroughMediator:
    def test_returns_input_unchanged(self):
        m = PassThroughMediator()
        assert m.mediate("hello") == "hello"

    def test_returns_none_unchanged(self):
        m = PassThroughMediator()
        assert m.mediate(None) is None

    def test_returns_dict_unchanged(self):
        m = PassThroughMediator()
        data = {"key": "value"}
        assert m.mediate(data) == data

    def test_returns_list_unchanged(self):
        m = PassThroughMediator()
        data = [1, 2, 3]
        assert m.mediate(data) == data

    def test_returns_number_unchanged(self):
        m = PassThroughMediator()
        assert m.mediate(42) == 42

    def test_inherits_from_mediator(self):
        assert issubclass(PassThroughMediator, Mediator)


class TestLoggingMediator:
    def test_returns_input_unchanged(self):
        m = LoggingMediator()
        assert m.mediate("hello") == "hello"

    def test_returns_none_unchanged(self):
        m = LoggingMediator()
        assert m.mediate(None) is None

    def test_returns_dict_unchanged(self):
        m = LoggingMediator()
        data = {"key": "value"}
        assert m.mediate(data) == data

    def test_inherits_from_mediator(self):
        assert issubclass(LoggingMediator, Mediator)

    def test_returns_complex_data_unchanged(self):
        m = LoggingMediator()
        data = {"nested": {"key": [1, 2, 3]}}
        assert m.mediate(data) == data
