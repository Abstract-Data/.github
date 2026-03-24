#!/usr/bin/env python3
"""
Integration and cross-validation tests for configuration files.

This module uses Hypothesis to test interactions between the markdownlint
configuration and the GitHub Actions workflow, ensuring they work together
correctly through property-based and stateful testing.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Set

import pytest
import yaml
from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize, precondition


# File paths
CONFIG_PATH = Path(__file__).parent.parent / ".markdownlint.json"
WORKFLOW_PATH = Path(__file__).parent.parent / ".github/workflows/update-profile.yml"
PROFILE_README_PATH = Path(__file__).parent.parent / "profile/README.md"


class TestConfigWorkflowIntegration:
    """Test integration between markdownlint config and workflow."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def workflow_data(self):
        """Load workflow configuration."""
        with open(WORKFLOW_PATH, 'r') as f:
            return yaml.safe_load(f)

    def test_workflow_references_existing_config(self, workflow_data):
        """Verify workflow references an existing configuration file."""
        workflow_str = yaml.dump(workflow_data)
        assert ".markdownlint.json" in workflow_str, \
            "Workflow must reference markdownlint config"
        assert CONFIG_PATH.exists(), \
            "Referenced config file must exist"

    def test_config_location_matches_workflow_reference(self, workflow_data):
        """Verify config file location matches workflow reference."""
        workflow_str = yaml.dump(workflow_data)
        # Extract config reference
        if "--config .markdownlint.json" in workflow_str:
            # Config should be at repo root (relative to workflow execution)
            assert CONFIG_PATH.name == ".markdownlint.json", \
                "Config filename must match workflow reference"
            assert CONFIG_PATH.parent.name == "git" or CONFIG_PATH.parent.parent.name == "git", \
                "Config must be at repository root"

    def test_workflow_validates_file_with_appropriate_config(self, workflow_data, config_data):
        """Verify workflow validates markdown with appropriate line length config."""
        # Get line length from config
        line_length = config_data["MD013"]["line_length"]
        
        # Workflow should validate profile/README.md
        workflow_str = yaml.dump(workflow_data)
        assert "profile/README.md" in workflow_str, \
            "Workflow should validate profile README"
        
        # Line length should be reasonable for the content being validated
        assert line_length >= 80, \
            "Line length should accommodate typical markdown content"
        assert line_length <= 1000, \
            "Line length should not be excessively large"

    def test_disabled_rules_appropriate_for_workflow(self, config_data):
        """Verify disabled rules are appropriate for the validation task."""
        disabled_rules = {
            "MD033": "inline-html",
            "MD041": "first-line-heading",
            "MD022": "blanks-around-headings",
            "MD032": "blanks-around-lists"
        }
        
        for rule_code, rule_desc in disabled_rules.items():
            assert rule_code in config_data, f"{rule_code} should be configured"
            assert config_data[rule_code] is False, \
                f"{rule_code} ({rule_desc}) should be disabled"

    def test_config_json_parseable_by_markdownlint_cli2(self, config_data):
        """Verify config structure is compatible with markdownlint-cli2."""
        # markdownlint-cli2 expects specific structure
        assert isinstance(config_data, dict), "Config must be object"
        
        # Check for valid rule configurations
        for key, value in config_data.items():
            if key == "default":
                assert isinstance(value, bool), "'default' must be boolean"
            elif key.startswith("MD"):
                assert isinstance(value, (bool, dict)), \
                    f"Rule {key} must be boolean or object"


class TestConfigurationConsistency:
    """Test consistency across configuration and workflow."""

    @given(st.sampled_from([
        "markdownlint-cli2",
        ".markdownlint.json",
        "profile/README.md",
        "--config"
    ]))
    def test_expected_tokens_present(self, token):
        """Property: Expected tokens should be present in workflow."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow_content = f.read()
        
        assert token in workflow_content, \
            f"Workflow should contain '{token}'"

    @given(st.sampled_from(["MD013", "MD033", "MD041", "MD022", "MD032"]))
    def test_configured_rules_are_valid(self, rule_code):
        """Property: All configured rules should be valid markdownlint rules."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        if rule_code in config:
            # Rule is configured
            value = config[rule_code]
            assert isinstance(value, (bool, dict)), \
                f"Rule {rule_code} must be boolean or object"

    @given(st.integers(min_value=1, max_value=5))
    def test_workflow_step_count_reasonable(self, min_steps):
        """Property: Workflow should have reasonable number of steps."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        assert len(steps) >= min_steps, \
            f"Workflow should have at least {min_steps} steps"


class TestPathReferences:
    """Test path references across files are correct."""

    def test_all_referenced_paths_valid(self):
        """Verify all paths referenced in workflow are valid or reasonable."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        referenced_paths = set()
        
        for step in steps:
            run_command = step.get("run", "")
            # Extract potential file paths
            if "profile/README.md" in run_command:
                referenced_paths.add("profile/README.md")
            if ".markdownlint.json" in run_command:
                referenced_paths.add(".markdownlint.json")
        
        # Verify config exists
        if ".markdownlint.json" in referenced_paths:
            assert CONFIG_PATH.exists(), "Config file must exist"

    @given(st.sampled_from([".markdownlint.json", "profile/README.md"]))
    def test_path_references_use_relative_paths(self, filename):
        """Property: Path references should use relative paths."""
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        
        if filename in content:
            # Should not start with /
            assert f"/{filename}" not in content or content.count(f"/{filename}") == 0, \
                f"Path to {filename} should be relative"

    def test_config_path_relative_to_workflow(self):
        """Verify config path is correct relative to workflow execution."""
        # Workflow executes from repo root
        # Config should be at repo root
        assert CONFIG_PATH.name == ".markdownlint.json"
        
        # Workflow references it as .markdownlint.json (repo root)
        with open(WORKFLOW_PATH, 'r') as f:
            workflow_content = f.read()
        
        assert "--config .markdownlint.json" in workflow_content


class IntegrationStateMachine(RuleBasedStateMachine):
    """Stateful testing for integration between config and workflow."""

    def __init__(self):
        super().__init__()
        self.config = None
        self.workflow = None
        self.validation_results = []

    @initialize()
    def load_files(self):
        """Initialize by loading both files."""
        with open(CONFIG_PATH, 'r') as f:
            self.config = json.load(f)
        with open(WORKFLOW_PATH, 'r') as f:
            self.workflow = yaml.safe_load(f)

    @rule()
    def verify_config_referenced_in_workflow(self):
        """Rule: Config file should be referenced in workflow."""
        workflow_str = yaml.dump(self.workflow)
        assert ".markdownlint.json" in workflow_str, \
            "Workflow must reference config"
        self.validation_results.append("config_referenced")

    @rule()
    def verify_config_structure_valid(self):
        """Rule: Config structure should always be valid."""
        assert isinstance(self.config, dict), "Config must be dict"
        assert "default" in self.config, "Config must have default"
        assert "MD013" in self.config, "Config must have MD013"
        self.validation_results.append("config_valid")

    @rule()
    def verify_workflow_has_validation_step(self):
        """Rule: Workflow should have markdown validation step."""
        steps = self.workflow["jobs"]["refresh-profile"]["steps"]
        has_validation = any(
            "markdown" in step.get("name", "").lower()
            for step in steps
        )
        assert has_validation, "Workflow must have validation step"
        self.validation_results.append("validation_step_exists")

    @rule()
    def verify_line_length_configuration(self):
        """Rule: Line length should be consistently configured."""
        line_length = self.config["MD013"]["line_length"]
        assert isinstance(line_length, int), "Line length must be int"
        assert line_length > 0, "Line length must be positive"
        self.validation_results.append(f"line_length_{line_length}")

    @rule(rule_code=st.sampled_from(["MD033", "MD041", "MD022", "MD032"]))
    def verify_rule_configuration(self, rule_code):
        """Rule: Disabled rules should be consistently configured."""
        if rule_code in self.config:
            assert self.config[rule_code] is False, \
                f"{rule_code} should be disabled"
            self.validation_results.append(f"rule_{rule_code}_verified")

    @invariant()
    def both_files_loaded(self):
        """Invariant: Both files should remain loaded."""
        assert self.config is not None, "Config must be loaded"
        assert self.workflow is not None, "Workflow must be loaded"

    @invariant()
    def validation_results_accumulating(self):
        """Invariant: Validation results should accumulate."""
        assert isinstance(self.validation_results, list), \
            "Results must be list"


TestIntegrationStateful = IntegrationStateMachine.TestCase


class TestCommandLineIntegration:
    """Test the actual command line integration."""

    def test_markdownlint_command_structure(self):
        """Verify markdownlint command has correct structure."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        markdownlint_step = None
        
        for step in steps:
            if "markdown" in step.get("name", "").lower():
                markdownlint_step = step
                break
        
        assert markdownlint_step is not None, "Must have markdownlint step"
        
        command = markdownlint_step.get("run", "")
        # Verify command structure
        assert "npx" in command, "Should use npx"
        assert "--yes" in command, "Should use --yes flag"
        assert "markdownlint-cli2" in command, "Should use markdownlint-cli2"
        assert "--config" in command, "Should use --config flag"
        assert ".markdownlint.json" in command, "Should reference config file"
        assert "profile/README.md" in command, "Should validate README"

    @given(st.sampled_from(["npx", "--yes", "markdownlint-cli2", "--config"]))
    def test_command_components_present(self, component):
        """Property: All command components should be present."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        workflow_str = yaml.dump(workflow)
        assert component in workflow_str, \
            f"Command should include '{component}'"

    def test_command_order_logical(self):
        """Verify command components are in logical order."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        for step in steps:
            if "markdown" in step.get("name", "").lower():
                command = step.get("run", "")
                
                # Find positions
                npx_pos = command.find("npx")
                config_pos = command.find("--config")
                file_pos = command.find("profile/README.md")
                
                if npx_pos >= 0 and config_pos >= 0 and file_pos >= 0:
                    # npx should come before --config
                    assert npx_pos < config_pos, \
                        "npx should come before --config"
                    # --config should come before file
                    assert config_pos < file_pos, \
                        "--config should come before target file"


class TestConfigurationValidation:
    """Test configuration validation logic."""

    @given(st.integers(min_value=1, max_value=1000))
    def test_line_length_range_validity(self, test_length):
        """Property: Config line length should be within valid range."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        line_length = config["MD013"]["line_length"]
        # Should be comparable and valid
        assert isinstance(line_length, int), "Line length must be int"
        assert line_length > 0, "Line length must be positive"

    @given(st.booleans())
    def test_boolean_configurations_valid(self, test_bool):
        """Property: Boolean configurations should be valid booleans."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Test default
        assert isinstance(config["default"], bool), \
            "'default' must be boolean"
        
        # Test MD013 booleans
        md013 = config["MD013"]
        assert isinstance(md013["code_blocks"], bool), \
            "code_blocks must be boolean"
        assert isinstance(md013["tables"], bool), \
            "tables must be boolean"

    @given(st.dictionaries(
        keys=st.sampled_from(["line_length", "code_blocks", "tables"]),
        values=st.one_of(st.integers(min_value=1), st.booleans()),
        min_size=1,
        max_size=3
    ))
    def test_md013_structure_flexibility(self, test_config):
        """Property: MD013 should have flexible but valid structure."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        md013 = config["MD013"]
        # Verify it has valid structure
        assert "line_length" in md013, "Must have line_length"
        assert "code_blocks" in md013, "Must have code_blocks"
        assert "tables" in md013, "Must have tables"


class TestErrorConditions:
    """Test error conditions and edge cases."""

    def test_config_handles_missing_optional_fields(self):
        """Verify config doesn't require optional fields."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # Config should work with just required fields
        required_fields = {"default", "MD013"}
        assert all(field in config for field in required_fields), \
            "Required fields must be present"

    def test_workflow_yaml_not_malformed(self):
        """Verify workflow YAML is well-formed."""
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        
        # Should parse without error
        parsed = yaml.safe_load(content)
        assert parsed is not None, "YAML must parse successfully"
        
        # Should be dict
        assert isinstance(parsed, dict), "Root should be dict"

    def test_config_json_not_malformed(self):
        """Verify config JSON is well-formed."""
        with open(CONFIG_PATH, 'r') as f:
            content = f.read()
        
        # Should parse without error
        parsed = json.loads(content)
        assert parsed is not None, "JSON must parse successfully"
        
        # Should be dict
        assert isinstance(parsed, dict), "Root should be dict"

    @given(st.text(min_size=0, max_size=100))
    def test_config_parsing_robust(self, extra_text):
        """Property: Config parsing should be robust."""
        # Actual config should always parse correctly
        with open(CONFIG_PATH, 'r') as f:
            content = f.read()
        
        parsed = json.loads(content)
        assert isinstance(parsed, dict), "Must parse to dict"
        
        # Re-serializing and parsing should yield same structure
        reserialized = json.dumps(parsed)
        reparsed = json.loads(reserialized)
        assert parsed.keys() == reparsed.keys(), \
            "Keys should be consistent after reparse"


class TestFilePermissionsAndAccess:
    """Test file permissions and access patterns."""

    def test_config_file_readable(self):
        """Verify config file is readable."""
        assert CONFIG_PATH.exists(), "Config file must exist"
        assert CONFIG_PATH.is_file(), "Config must be a file"
        assert CONFIG_PATH.stat().st_size > 0, "Config must not be empty"

    def test_workflow_file_readable(self):
        """Verify workflow file is readable."""
        assert WORKFLOW_PATH.exists(), "Workflow file must exist"
        assert WORKFLOW_PATH.is_file(), "Workflow must be a file"
        assert WORKFLOW_PATH.stat().st_size > 0, "Workflow must not be empty"

    def test_files_have_appropriate_extensions(self):
        """Verify files have correct extensions."""
        assert CONFIG_PATH.suffix == ".json", "Config should be .json"
        assert WORKFLOW_PATH.suffix == ".yml", "Workflow should be .yml"

    def test_config_location_standard(self):
        """Verify config is in standard location."""
        # Should be at repo root with dot prefix (hidden file)
        assert CONFIG_PATH.name.startswith("."), \
            "Config should be hidden file (dot prefix)"
        assert "markdownlint" in CONFIG_PATH.name, \
            "Config name should indicate markdownlint"


class TestSemanticConsistency:
    """Test semantic consistency between files."""

    def test_disabled_rules_semantic_meaning(self):
        """Verify disabled rules make semantic sense together."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        # MD022 and MD032 are both spacing-related
        if "MD022" in config and "MD032" in config:
            # Both are disabled, which is semantically consistent
            assert config["MD022"] == config["MD032"], \
                "Related spacing rules should have consistent config"

    def test_line_length_semantic_appropriateness(self):
        """Verify line length is semantically appropriate."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        line_length = config["MD013"]["line_length"]
        
        # 350 is reasonable for markdown with long URLs/paths
        assert 80 <= line_length <= 500, \
            "Line length should be in reasonable range for markdown"

    def test_code_blocks_and_tables_exclusion_semantic(self):
        """Verify code blocks and tables exclusion makes sense."""
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        
        md013 = config["MD013"]
        # Excluding code blocks and tables from line length is common
        assert md013["code_blocks"] is False, \
            "Code blocks commonly excluded from line length"
        assert md013["tables"] is False, \
            "Tables commonly excluded from line length"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])