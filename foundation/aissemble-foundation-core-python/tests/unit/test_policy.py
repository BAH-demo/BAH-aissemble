import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from policy_manager.policy.policy import (
    AlertOptions,
    Target,
    ConfiguredTarget,
    ConfiguredRule,
    Policy,
)


class TestAlertOptions:
    def test_always_value(self):
        assert AlertOptions.ALWAYS.value == "ALWAYS"

    def test_on_detection_value(self):
        assert AlertOptions.ON_DETECTION.value == "ON_DETECTION"

    def test_never_value(self):
        assert AlertOptions.NEVER.value == "NEVER"

    def test_enum_members(self):
        assert len(AlertOptions) == 3


class TestTarget:
    def test_default_values(self):
        target = Target()
        assert target.retrieve_url is None
        assert target.type is None

    def test_custom_values(self):
        target = Target(retrieve_url="http://data-source", type="REST")
        assert target.retrieve_url == "http://data-source"
        assert target.type == "REST"


class TestConfiguredTarget:
    def test_with_configurations(self):
        ct = ConfiguredTarget(
            target_configurations={"param1": "val1"},
            retrieve_url="http://example.com",
            type="S3",
        )
        assert ct.target_configurations == {"param1": "val1"}
        assert ct.retrieve_url == "http://example.com"
        assert ct.type == "S3"

    def test_inherits_from_target(self):
        assert issubclass(ConfiguredTarget, Target)

    def test_empty_configurations(self):
        ct = ConfiguredTarget(target_configurations={})
        assert ct.target_configurations == {}


class TestConfiguredRule:
    def test_create_rule(self):
        rule = ConfiguredRule(className="com.example.MyRule")
        assert rule.className == "com.example.MyRule"
        assert rule.configurations is None
        assert rule.configuredTargets == []

    def test_rule_with_configurations(self):
        rule = ConfiguredRule(
            className="com.example.MyRule",
            configurations={"threshold": 0.5},
        )
        assert rule.configurations["threshold"] == 0.5

    def test_rule_with_configured_targets(self):
        ct = ConfiguredTarget(target_configurations={"key": "val"})
        rule = ConfiguredRule(
            className="com.example.MyRule",
            configuredTargets=[ct],
        )
        assert len(rule.configuredTargets) == 1

    def test_deprecated_target_configurations_getter_raises_attribute_error(self):
        ct = ConfiguredTarget(target_configurations={"key": "val"})
        rule = ConfiguredRule(
            className="com.example.MyRule",
            configuredTargets=[ct],
        )
        with pytest.raises(AttributeError):
            _ = rule.targetConfigurations

    def test_deprecated_set_target_configurations_raises_attribute_error(self):
        rule = ConfiguredRule(className="com.example.MyRule")
        ct = ConfiguredTarget(target_configurations={"new": "config"})
        with pytest.raises(AttributeError):
            rule.set_deprecated_targetConfigurations(ct)


class TestPolicy:
    def test_create_policy(self):
        policy = Policy(identifier="test-policy")
        assert policy.identifier == "test-policy"
        assert policy.alertOptions == AlertOptions.ON_DETECTION
        assert policy.description is None
        assert policy.targets == []
        assert policy.rules == []

    def test_policy_with_alert_options(self):
        policy = Policy(
            identifier="alert-policy",
            alertOptions=AlertOptions.ALWAYS,
        )
        assert policy.alertOptions == AlertOptions.ALWAYS

    def test_policy_with_targets(self):
        targets = [
            Target(retrieve_url="http://a", type="REST"),
            Target(retrieve_url="http://b", type="S3"),
        ]
        policy = Policy(identifier="multi-target", targets=targets)
        assert len(policy.targets) == 2

    def test_policy_with_rules(self):
        rules = [
            ConfiguredRule(className="Rule1"),
            ConfiguredRule(className="Rule2"),
        ]
        policy = Policy(identifier="rules-policy", rules=rules)
        assert len(policy.rules) == 2

    def test_deprecated_target_getter_raises_attribute_error(self):
        target = Target(retrieve_url="http://a", type="T")
        policy = Policy(identifier="dep-test", targets=[target])
        with pytest.raises(AttributeError):
            _ = policy.target

    def test_deprecated_set_target_raises_attribute_error(self):
        policy = Policy(identifier="dep-test")
        target = Target(retrieve_url="http://new", type="NEW")
        with pytest.raises(AttributeError):
            policy.set_deprecated_target(target)

    def test_policy_description(self):
        policy = Policy(
            identifier="desc-policy",
            description="A test policy description",
        )
        assert policy.description == "A test policy description"
