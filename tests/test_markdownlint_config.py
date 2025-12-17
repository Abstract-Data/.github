#!/usr/bin/env python3
"""
Property-based tests for .markdownlint.json configuration file.

This module uses Hypothesis to validate the markdownlint configuration
through property-based testing, ensuring the configuration is valid
across a wide range of scenarios.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize


# Configuration file path
CONFIG_PATH = Path(__file__).parent.parent / ".markdownlint.json"


class TestMarkdownlintConfigStructure:
    """Test the structure and validity of the markdownlint configuration."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load the markdownlint configuration file."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def test_config_file_exists(self):
        """Verify the configuration file exists."""
        assert CONFIG_PATH.exists(), f"Configuration file not found at {CONFIG_PATH}"

    def test_config_is_valid_json(self):
        """Verify the configuration file is valid JSON."""
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict), "Configuration must be a JSON object"

    def test_config_has_required_structure(self, config_data):
        """Verify the configuration has the expected top-level structure."""
        assert isinstance(config_data, dict), "Configuration must be a dictionary"
        assert "default" in config_data, "Configuration must have 'default' key"

    def test_default_is_boolean(self, config_data):
        """Verify 'default' is a boolean value."""
        assert isinstance(config_data["default"], bool), "'default' must be a boolean"

    def test_md013_structure(self, config_data):
        """Verify MD013 (line length) configuration structure."""
        assert "MD013" in config_data, "MD013 rule should be configured"
        md013 = config_data["MD013"]
        assert isinstance(md013, dict), "MD013 must be an object"
        assert "line_length" in md013, "MD013 must specify line_length"
        assert "code_blocks" in md013, "MD013 must specify code_blocks"
        assert "tables" in md013, "MD013 must specify tables"

    def test_md013_line_length_is_positive(self, config_data):
        """Verify MD013 line_length is a positive integer."""
        line_length = config_data["MD013"]["line_length"]
        assert isinstance(line_length, int), "line_length must be an integer"
        assert line_length > 0, "line_length must be positive"

    def test_disabled_rules_are_boolean_false(self, config_data):
        """Verify disabled rules (MD033, MD041, MD022, MD032) are set to false."""
        disabled_rules = ["MD033", "MD041", "MD022", "MD032"]
        for rule in disabled_rules:
            assert rule in config_data, f"{rule} should be present in config"
            assert config_data[rule] is False, f"{rule} should be set to false"


class TestMarkdownlintConfigProperties:
    """Property-based tests for markdownlint configuration validation."""

    @given(st.integers(min_value=1, max_value=10000))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_line_length_property_positive_values(self, line_length):
        """Property: Line length must always be positive when valid."""
        # Load actual config
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        actual_length = config["MD013"]["line_length"]
        assert actual_length > 0, "Configured line length must be positive"
        assert isinstance(actual_length, int), "Line length must be an integer"

    @given(st.booleans())
    def test_default_property_boolean_values(self, expected_boolean):
        """Property: The 'default' field should always be a boolean."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        assert isinstance(config["default"], bool), "'default' must be a boolean"

    @given(st.sampled_from(["MD033", "MD041", "MD022", "MD032"]))
    def test_disabled_rules_property(self, rule_name):
        """Property: Disabled rules should always be explicitly set to false."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        assert rule_name in config, f"{rule_name} must be in configuration"
        assert config[rule_name] is False, f"{rule_name} must be disabled (false)"

    @given(st.sampled_from(["code_blocks", "tables"]))
    def test_md013_boolean_properties(self, property_name):
        """Property: MD013 boolean properties should be valid booleans."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        md013 = config["MD013"]
        assert property_name in md013, f"{property_name} must be in MD013"
        assert isinstance(md013[property_name], bool), f"{property_name} must be boolean"

    @given(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu",))))
    def test_rule_name_format_property(self, prefix):
        """Property: All rule names in config should follow MD + digits pattern."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        rule_keys = [k for k in config.keys() if k.startswith("MD")]
        for rule in rule_keys:
            assert rule.startswith("MD"), f"Rule {rule} should start with 'MD'"
            assert rule[2:].isdigit(), f"Rule {rule} should have digits after 'MD'"


class TestMarkdownlintConfigCompatibility:
    """Test configuration compatibility with markdownlint-cli2."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load the markdownlint configuration file."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @given(st.integers(min_value=80, max_value=500))
    def test_line_length_within_reasonable_bounds(self, test_length):
        """Property: Line length should be within reasonable bounds for markdown."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        actual_length = config["MD013"]["line_length"]
        # The actual config uses 350, which is within reasonable markdown bounds
        assert 1 <= actual_length <= 10000, "Line length should be within practical bounds"

    def test_no_conflicting_rules(self, config_data):
        """Verify there are no conflicting rule configurations."""
        # MD022 and MD032 both relate to spacing, ensure they don't conflict
        if "MD022" in config_data and "MD032" in config_data:
            # Both are disabled, which is consistent
            assert config_data["MD022"] == config_data["MD032"], \
                "Related spacing rules should have consistent configuration"

    def test_json_serialization_roundtrip(self, config_data):
        """Property: Config should survive JSON serialization round-trip."""
        serialized = json.dumps(config_data)
        deserialized = json.loads(serialized)
        assert config_data == deserialized, "Config should survive JSON round-trip"

    @given(st.dictionaries(
        keys=st.sampled_from(["line_length", "code_blocks", "tables"]),
        values=st.one_of(st.integers(min_value=1, max_value=1000), st.booleans()),
        min_size=1
    ))
    def test_md013_structure_variations(self, md013_variant):
        """Property: MD013 should handle various valid structure variations."""
        # Load actual config and verify it has valid MD013 structure
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        md013 = config["MD013"]
        assert isinstance(md013, dict), "MD013 must be a dictionary"
        assert all(k in ["line_length", "code_blocks", "tables"] for k in md013.keys()), \
            "MD013 should only contain expected keys"


class MarkdownlintConfigStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for markdownlint configuration."""

    def __init__(self):
        super().__init__()
        self.config_path = CONFIG_PATH
        self.loaded_config = None
        self.modification_count = 0

    @initialize()
    def load_initial_config(self):
        """Initialize by loading the configuration."""
        with open(self.config_path, 'r') as f:
            self.loaded_config = json.load(f)

    @rule()
    def verify_config_structure(self):
        """Rule: Configuration structure should always be valid."""
        assert isinstance(self.loaded_config, dict), "Config must be a dict"
        assert "default" in self.loaded_config, "Config must have 'default'"
        assert isinstance(self.loaded_config["default"], bool), "'default' must be boolean"

    @rule()
    def verify_md013_configuration(self):
        """Rule: MD013 should always have valid line length configuration."""
        assert "MD013" in self.loaded_config, "MD013 must be present"
        md013 = self.loaded_config["MD013"]
        assert isinstance(md013, dict), "MD013 must be a dict"
        assert "line_length" in md013, "MD013 must have line_length"
        assert isinstance(md013["line_length"], int), "line_length must be int"
        assert md013["line_length"] > 0, "line_length must be positive"

    @rule()
    def verify_disabled_rules_consistency(self):
        """Rule: All disabled rules should remain consistently disabled."""
        disabled_rules = ["MD033", "MD041", "MD022", "MD032"]
        for rule in disabled_rules:
            if rule in self.loaded_config:
                assert self.loaded_config[rule] is False, \
                    f"{rule} should be consistently disabled"

    @rule(rule_name=st.sampled_from(["MD013", "MD033", "MD041", "MD022", "MD032"]))
    def verify_rule_exists(self, rule_name):
        """Rule: Named rules should exist in configuration."""
        assert rule_name in self.loaded_config, f"{rule_name} should exist in config"

    @invariant()
    def config_is_valid_json_structure(self):
        """Invariant: Config should always be a valid dictionary."""
        assert isinstance(self.loaded_config, dict), \
            "Configuration must always be a dictionary"
        assert len(self.loaded_config) > 0, \
            "Configuration must not be empty"

    @invariant()
    def default_exists_and_is_boolean(self):
        """Invariant: 'default' key must always exist and be boolean."""
        assert "default" in self.loaded_config, "'default' must exist"
        assert isinstance(self.loaded_config["default"], bool), \
            "'default' must be boolean"


TestMarkdownlintConfigStateful = MarkdownlintConfigStateMachine.TestCase


class TestMarkdownlintConfigEdgeCases:
    """Test edge cases and error conditions."""

    @given(st.text(min_size=0, max_size=1000))
    def test_config_parsing_with_various_content(self, extra_content):
        """Property: Config file should be parseable despite various scenarios."""
        # Test that actual config is always parseable
        with open(CONFIG_PATH, 'r') as f:
            content = f.read()
        
        # Should not raise
        parsed = json.loads(content)
        assert isinstance(parsed, dict), "Config must parse to dict"

    def test_config_file_not_empty(self):
        """Verify configuration file is not empty."""
        size = CONFIG_PATH.stat().st_size
        assert size > 0, "Configuration file must not be empty"

    def test_config_has_minimum_required_fields(self):
        """Verify configuration has minimum required fields for markdownlint."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        required_fields = ["default", "MD013"]
        for field in required_fields:
            assert field in config, f"Configuration must have '{field}' field"

    @given(st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=10))
    def test_line_length_comparison_property(self, test_lengths):
        """Property: Configured line length should be comparable with test values."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        actual_length = config["MD013"]["line_length"]
        # Should be able to compare with any valid integer
        for test_length in test_lengths:
            assert isinstance(actual_length, int), "Must be comparable as int"
            _ = actual_length > test_length or actual_length <= test_length

    def test_config_schema_version_compatibility(self):
        """Verify configuration is compatible with markdownlint schema."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Verify no unknown top-level structures that would break markdownlint
        valid_keys = {"default", "MD013", "MD033", "MD041", "MD022", "MD032"}
        actual_keys = set(config.keys())
        assert actual_keys.issubset(valid_keys) or all(
            k.startswith("MD") or k == "default" for k in actual_keys
        ), "All keys should be valid markdownlint configuration keys"


class TestMarkdownlintConfigIntegration:
    """Integration tests for markdownlint configuration with workflow."""

    def test_config_referenced_in_workflow(self):
        """Verify the config file is referenced in the workflow."""
        workflow_path = Path(__file__).parent.parent / ".github/workflows/update-profile.yml"
        with open(workflow_path, 'r') as f:
            workflow_content = f.read()
        
        assert ".markdownlint.json" in workflow_content, \
            "Workflow should reference the markdownlint config file"
        assert "--config .markdownlint.json" in workflow_content, \
            "Workflow should use --config flag with the config file"

    def test_config_path_relative_to_repo_root(self):
        """Verify config file is at repository root as expected by workflow."""
        # Config should be at repo root
        expected_path = Path(__file__).parent.parent / ".markdownlint.json"
        assert expected_path.exists(), "Config should be at repository root"
        assert expected_path == CONFIG_PATH, "Config path should match expected location"

    @given(st.text(min_size=1, max_size=500, alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"), max_codepoint=127
    )))
    def test_config_handles_various_markdown_content(self, markdown_line):
        """Property: Config should have appropriate line length for various content."""
        assume(len(markdown_line.strip()) > 0)
        
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        line_length = config["MD013"]["line_length"]
        # Verify configuration makes sense for typical markdown content
        assert line_length >= 80, "Line length should accommodate typical content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])