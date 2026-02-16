import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from data_transform_core.mediator.mediation_objects import (
    MediationException,
    MediationContext,
    MediationProperty,
    MediationConfiguration,
)


class TestMediationException:
    def test_inherits_from_exception(self):
        assert issubclass(MediationException, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(MediationException):
            raise MediationException("test error")

    def test_message_preserved(self):
        with pytest.raises(MediationException, match="my mediation error"):
            raise MediationException("my mediation error")


class TestMediationContext:
    def test_create_context(self):
        ctx = MediationContext(inputType="json", outputType="csv")
        assert ctx.inputType == "json"
        assert ctx.outputType == "csv"

    def test_hash_same_for_equal_contexts(self):
        ctx1 = MediationContext(inputType="json", outputType="csv")
        ctx2 = MediationContext(inputType="json", outputType="csv")
        assert hash(ctx1) == hash(ctx2)

    def test_hash_differs_for_different_contexts(self):
        ctx1 = MediationContext(inputType="json", outputType="csv")
        ctx2 = MediationContext(inputType="csv", outputType="json")
        assert hash(ctx1) != hash(ctx2)

    def test_context_can_be_used_as_dict_key(self):
        ctx = MediationContext(inputType="a", outputType="b")
        d = {ctx: "value"}
        lookup = MediationContext(inputType="a", outputType="b")
        assert d[lookup] == "value"

    def test_is_pydantic_model(self):
        from pydantic import BaseModel

        assert issubclass(MediationContext, BaseModel)


class TestMediationProperty:
    def test_create_property(self):
        prop = MediationProperty(key="delimiter", value=",")
        assert prop.key == "delimiter"
        assert prop.value == ","

    def test_different_properties(self):
        prop = MediationProperty(key="encoding", value="utf-8")
        assert prop.key == "encoding"
        assert prop.value == "utf-8"


class TestMediationConfiguration:
    def test_create_configuration(self):
        config = MediationConfiguration(
            inputType="json",
            outputType="csv",
            className="my_module.MyMediator",
        )
        assert config.inputType == "json"
        assert config.outputType == "csv"
        assert config.className == "my_module.MyMediator"
        assert config.properties is None

    def test_inherits_from_mediation_context(self):
        assert issubclass(MediationConfiguration, MediationContext)

    def test_get_short_class_name_with_package(self):
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="my_package.my_module.MyMediator",
        )
        assert config.getShortClassName() == "MyMediator"

    def test_get_short_class_name_without_package(self):
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="MyMediator",
        )
        assert config.getShortClassName() == "MyMediator"

    def test_get_package_name_with_package(self):
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="my_package.my_module.MyMediator",
        )
        assert config.getPackageName() == "my_package.my_module"

    def test_get_package_name_without_package(self):
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="MyMediator",
        )
        assert config.getPackageName() == ""

    def test_configuration_with_properties(self):
        props = [
            MediationProperty(key="k1", value="v1"),
            MediationProperty(key="k2", value="v2"),
        ]
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="pkg.Cls",
            properties=props,
        )
        assert len(config.properties) == 2
        assert config.properties[0].key == "k1"

    def test_get_short_class_name_single_dot(self):
        config = MediationConfiguration(
            inputType="a",
            outputType="b",
            className="module.Class",
        )
        assert config.getShortClassName() == "Class"
        assert config.getPackageName() == "module"
