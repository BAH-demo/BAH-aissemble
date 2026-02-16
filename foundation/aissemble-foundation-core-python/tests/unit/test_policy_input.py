import sys
import os

import pytest

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "src"
    ),
)

from policy_manager.policy.json.policy_input import PolicyInput, PolicyRuleInput
from policy_manager.policy.policy import AlertOptions, Target


class TestPolicyRuleInput:
    def test_create_rule_input(self):
        rule = PolicyRuleInput(className="com.example.Rule")
        assert rule.className == "com.example.Rule"
        assert rule.configurations is None
        assert rule.targetConfigurations is None

    def test_rule_input_with_configurations(self):
        rule = PolicyRuleInput(
            className="com.example.Rule",
            configurations={"key": "value"},
            targetConfigurations={"target_key": "target_value"},
        )
        assert rule.configurations == {"key": "value"}
        assert rule.targetConfigurations == {"target_key": "target_value"}


class TestPolicyInput:
    def test_create_policy_input(self):
        pi = PolicyInput(identifier="policy-1")
        assert pi.identifier == "policy-1"
        assert pi.description is None
        assert pi.targets is None
        assert pi.shouldSendAlert is None
        assert pi.rules == []
        assert pi.target is None

    def test_policy_input_with_all_fields(self):
        target = Target(retrieve_url="http://example.com", type="REST")
        rule = PolicyRuleInput(className="MyRule")
        pi = PolicyInput(
            identifier="policy-2",
            description="Test policy",
            targets=[target],
            shouldSendAlert=AlertOptions.ALWAYS,
            rules=[rule],
        )
        assert pi.description == "Test policy"
        assert len(pi.targets) == 1
        assert pi.shouldSendAlert == AlertOptions.ALWAYS
        assert len(pi.rules) == 1

    def test_get_any_targets_with_targets_list(self):
        targets = [Target(type="A"), Target(type="B")]
        pi = PolicyInput(identifier="p", targets=targets)
        result = pi.getAnyTargets()
        assert result == targets

    def test_get_any_targets_with_deprecated_target(self):
        target = Target(type="DEPRECATED")
        pi = PolicyInput(identifier="p", target=target)
        result = pi.getAnyTargets()
        assert len(result) == 1
        assert result[0].type == "DEPRECATED"

    def test_get_any_targets_with_none(self):
        pi = PolicyInput(identifier="p")
        result = pi.getAnyTargets()
        assert result is None

    def test_get_any_targets_deprecated_takes_precedence_over_none(self):
        target = Target(type="DEP")
        pi = PolicyInput(identifier="p", target=target, targets=None)
        result = pi.getAnyTargets()
        assert len(result) == 1
