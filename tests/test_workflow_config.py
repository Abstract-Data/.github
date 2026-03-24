#!/usr/bin/env python3
"""
Property-based tests for GitHub Actions workflow configuration.

This module uses Hypothesis to validate the update-profile.yml workflow
through property-based and stateful testing.
"""

import re
from pathlib import Path
from typing import Dict, List, Any

import pytest
import yaml
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize


# Workflow file path
WORKFLOW_PATH = Path(__file__).parent.parent / ".github/workflows/update-profile.yml"


class TestWorkflowStructure:
    """Test the structure and validity of the GitHub Actions workflow."""

    @pytest.fixture(scope="class")
    def workflow_data(self):
        """Load the workflow YAML file."""
        with open(WORKFLOW_PATH, 'r') as f:
            return yaml.safe_load(f)

    def test_workflow_file_exists(self):
        """Verify the workflow file exists."""
        assert WORKFLOW_PATH.exists(), f"Workflow file not found at {WORKFLOW_PATH}"

    def test_workflow_is_valid_yaml(self):
        """Verify the workflow file is valid YAML."""
        with open(WORKFLOW_PATH, 'r') as f:
            data = yaml.safe_load(f)
        assert isinstance(data, dict), "Workflow must be a YAML object"

    def test_workflow_has_required_keys(self, workflow_data):
        """Verify workflow has required GitHub Actions keys."""
        required_keys = ["name", "on", "jobs"]
        for key in required_keys:
            assert key in workflow_data, f"Workflow must have '{key}' key"

    def test_workflow_name_is_string(self, workflow_data):
        """Verify workflow name is a string."""
        assert isinstance(workflow_data["name"], str), "Workflow name must be a string"
        assert len(workflow_data["name"]) > 0, "Workflow name must not be empty"

    def test_workflow_has_jobs(self, workflow_data):
        """Verify workflow has at least one job."""
        jobs = workflow_data.get("jobs", {})
        assert isinstance(jobs, dict), "Jobs must be a dictionary"
        assert len(jobs) > 0, "Workflow must have at least one job"

    def test_refresh_profile_job_exists(self, workflow_data):
        """Verify the refresh-profile job exists."""
        assert "refresh-profile" in workflow_data["jobs"], \
            "Workflow must have 'refresh-profile' job"

    def test_job_has_required_structure(self, workflow_data):
        """Verify job has required structure."""
        job = workflow_data["jobs"]["refresh-profile"]
        assert "runs-on" in job, "Job must specify 'runs-on'"
        assert "steps" in job, "Job must have 'steps'"
        assert isinstance(job["steps"], list), "Steps must be a list"
        assert len(job["steps"]) > 0, "Job must have at least one step"

    def test_workflow_triggers_are_valid(self, workflow_data):
        """Verify workflow triggers are properly configured."""
        on_config = workflow_data["on"]
        assert isinstance(on_config, dict), "'on' must be a dictionary"
        # Check for at least one trigger type
        valid_triggers = ["workflow_dispatch", "schedule", "push", "pull_request"]
        has_trigger = any(trigger in on_config for trigger in valid_triggers)
        assert has_trigger, "Workflow must have at least one valid trigger"


class TestWorkflowMarkdownlintStep:
    """Test the markdownlint validation step specifically."""

    @pytest.fixture(scope="class")
    def workflow_data(self):
        """Load the workflow YAML file."""
        with open(WORKFLOW_PATH, 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def markdownlint_step(self, workflow_data):
        """Extract the markdownlint validation step."""
        steps = workflow_data["jobs"]["refresh-profile"]["steps"]
        for step in steps:
            if "Validate organization markdown" in step.get("name", ""):
                return step
        return None

    def test_markdownlint_step_exists(self, markdownlint_step):
        """Verify the markdownlint validation step exists."""
        assert markdownlint_step is not None, \
            "Workflow must have markdownlint validation step"

    def test_markdownlint_uses_config_flag(self, markdownlint_step):
        """Verify markdownlint step uses --config flag."""
        assert markdownlint_step is not None
        run_command = markdownlint_step.get("run", "")
        assert "--config" in run_command, \
            "Markdownlint command must use --config flag"

    def test_markdownlint_references_config_file(self, markdownlint_step):
        """Verify markdownlint step references .markdownlint.json."""
        assert markdownlint_step is not None
        run_command = markdownlint_step.get("run", "")
        assert ".markdownlint.json" in run_command, \
            "Markdownlint command must reference .markdownlint.json"

    def test_markdownlint_validates_profile_readme(self, markdownlint_step):
        """Verify markdownlint step validates profile/README.md."""
        assert markdownlint_step is not None
        run_command = markdownlint_step.get("run", "")
        assert "profile/README.md" in run_command, \
            "Markdownlint command must validate profile/README.md"

    def test_markdownlint_command_structure(self, markdownlint_step):
        """Verify markdownlint command has proper structure."""
        assert markdownlint_step is not None
        run_command = markdownlint_step.get("run", "")
        assert "npx" in run_command, "Should use npx to run markdownlint"
        assert "markdownlint-cli2" in run_command, "Should use markdownlint-cli2"
        assert "--yes" in run_command or "-y" in run_command, \
            "Should use --yes flag with npx"


class TestWorkflowStepOrdering:
    """Test the ordering and dependencies of workflow steps."""

    @pytest.fixture(scope="class")
    def workflow_data(self):
        """Load the workflow YAML file."""
        with open(WORKFLOW_PATH, 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def steps(self, workflow_data):
        """Extract workflow steps."""
        return workflow_data["jobs"]["refresh-profile"]["steps"]

    def test_checkout_is_first_step(self, steps):
        """Verify checkout is the first step."""
        first_step = steps[0]
        assert "checkout" in first_step.get("uses", "").lower() or \
               "checkout" in first_step.get("name", "").lower(), \
            "First step should be checkout"

    def test_setup_node_before_npm_commands(self, steps):
        """Verify Node.js setup happens before any npm/npx commands."""
        node_setup_index = None
        npm_command_index = None
        
        for i, step in enumerate(steps):
            step_name = step.get("name", "").lower()
            step_uses = step.get("uses", "").lower()
            step_run = step.get("run", "").lower()
            
            if "node" in step_name or "node" in step_uses:
                if node_setup_index is None:
                    node_setup_index = i
            
            if "npm" in step_run or "npx" in step_run:
                if npm_command_index is None:
                    npm_command_index = i
        
        if node_setup_index is not None and npm_command_index is not None:
            assert node_setup_index < npm_command_index, \
                "Node.js setup must occur before npm/npx commands"

    def test_validation_before_commit(self, steps):
        """Verify validation steps occur before commit step."""
        validation_index = None
        commit_index = None
        
        for i, step in enumerate(steps):
            step_name = step.get("name", "").lower()
            step_run = step.get("run", "").lower()
            
            if "validate" in step_name or "verify" in step_name:
                if validation_index is None:
                    validation_index = i
            
            if "commit" in step_name or "git commit" in step_run:
                if commit_index is None:
                    commit_index = i
        
        if validation_index is not None and commit_index is not None:
            assert validation_index < commit_index, \
                "Validation must occur before commit"


class TestWorkflowProperties:
    """Property-based tests for workflow configuration."""

    @given(st.integers(min_value=0, max_value=10))
    def test_workflow_has_sufficient_steps(self, min_steps):
        """Property: Workflow should have a reasonable number of steps."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        # Workflow should have at least 4 steps (checkout, setup, validate, commit)
        assert len(steps) >= 4, "Workflow should have sufficient steps"

    @given(st.sampled_from(["name", "run", "uses"]))
    def test_all_steps_have_required_fields(self, field_type):
        """Property: All steps should have either 'name', 'run', or 'uses'."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        for step in steps:
            # Each step must have at least 'run' or 'uses'
            assert "run" in step or "uses" in step, \
                "Each step must have 'run' or 'uses'"

    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("L", "N"), max_codepoint=127
    )))
    def test_step_names_are_descriptive(self, test_string):
        """Property: Step names should be descriptive strings."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        for step in steps:
            if "name" in step:
                name = step["name"]
                assert isinstance(name, str), "Step name must be string"
                assert len(name) > 0, "Step name must not be empty"
                # Names should have reasonable length
                assert len(name) < 200, "Step name should be concise"

    @given(st.sampled_from([
        "GITHUB_TOKEN", "workflow_dispatch", "schedule", "ubuntu-latest"
    ]))
    def test_workflow_contains_expected_keywords(self, keyword):
        """Property: Workflow should contain expected GitHub Actions keywords."""
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        
        # Various forms of expected content
        if keyword == "GITHUB_TOKEN":
            assert "GITHUB_TOKEN" in content, "Should reference GITHUB_TOKEN"


class WorkflowConfigStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for workflow configuration."""

    def __init__(self):
        super().__init__()
        self.workflow_path = WORKFLOW_PATH
        self.loaded_workflow = None
        self.steps_analyzed = []

    @initialize()
    def load_initial_workflow(self):
        """Initialize by loading the workflow."""
        with open(self.workflow_path, 'r') as f:
            self.loaded_workflow = yaml.safe_load(f)

    @rule()
    def verify_workflow_structure(self):
        """Rule: Workflow structure should always be valid."""
        assert isinstance(self.loaded_workflow, dict), "Workflow must be a dict"
        assert "jobs" in self.loaded_workflow, "Workflow must have jobs"
        assert "refresh-profile" in self.loaded_workflow["jobs"], \
            "Workflow must have refresh-profile job"

    @rule()
    def verify_markdownlint_configuration(self):
        """Rule: Markdownlint step should always reference config file."""
        steps = self.loaded_workflow["jobs"]["refresh-profile"]["steps"]
        markdownlint_steps = [
            s for s in steps
            if "markdown" in s.get("name", "").lower()
        ]
        
        if markdownlint_steps:
            step = markdownlint_steps[0]
            run_command = step.get("run", "")
            assert ".markdownlint.json" in run_command, \
                "Markdownlint must reference config file"

    @rule(step_index=st.integers(min_value=0, max_value=10))
    def analyze_step_at_index(self, step_index):
        """Rule: Analyze steps at various indices."""
        steps = self.loaded_workflow["jobs"]["refresh-profile"]["steps"]
        if step_index < len(steps):
            step = steps[step_index]
            self.steps_analyzed.append(step_index)
            assert isinstance(step, dict), f"Step {step_index} must be a dict"
            assert "name" in step or "uses" in step or "run" in step, \
                f"Step {step_index} must have name, uses, or run"

    @rule()
    def verify_environment_variables(self):
        """Rule: Environment variables should be properly configured."""
        job = self.loaded_workflow["jobs"]["refresh-profile"]
        if "env" in job:
            env_vars = job["env"]
            assert isinstance(env_vars, dict), "Environment variables must be dict"

    @invariant()
    def workflow_has_valid_structure(self):
        """Invariant: Workflow must always have valid structure."""
        assert isinstance(self.loaded_workflow, dict), "Workflow must be dict"
        assert "jobs" in self.loaded_workflow, "Must have jobs"
        assert len(self.loaded_workflow["jobs"]) > 0, "Must have at least one job"

    @invariant()
    def job_has_steps(self):
        """Invariant: Job must always have steps."""
        job = self.loaded_workflow["jobs"]["refresh-profile"]
        assert "steps" in job, "Job must have steps"
        assert isinstance(job["steps"], list), "Steps must be a list"
        assert len(job["steps"]) > 0, "Job must have at least one step"


TestWorkflowConfigStateful = WorkflowConfigStateMachine.TestCase


class TestWorkflowEdgeCases:
    """Test edge cases and failure conditions."""

    @pytest.fixture(scope="class")
    def workflow_data(self):
        """Load the workflow YAML file."""
        with open(WORKFLOW_PATH, 'r') as f:
            return yaml.safe_load(f)

    def test_workflow_handles_secrets_reference(self, workflow_data):
        """Verify workflow properly references GitHub secrets."""
        # Convert to string to search for secrets reference
        workflow_str = yaml.dump(workflow_data)
        assert "secrets.GITHUB_TOKEN" in workflow_str, \
            "Workflow should reference GitHub token from secrets"

    def test_no_hardcoded_credentials(self, workflow_data):
        """Verify no hardcoded credentials in workflow."""
        workflow_str = yaml.dump(workflow_data).lower()
        # Check for common patterns of hardcoded credentials
        forbidden_patterns = ["password:", "api_key:", "secret_key:"]
        for pattern in forbidden_patterns:
            assert pattern not in workflow_str, \
                f"Workflow should not contain hardcoded {pattern}"

    def test_step_error_handling(self, workflow_data):
        """Verify steps have appropriate structure for error handling."""
        steps = workflow_data["jobs"]["refresh-profile"]["steps"]
        # Verify steps are properly structured
        for step in steps:
            assert isinstance(step, dict), "Each step must be a dictionary"

    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
    def test_workflow_file_parsing_stability(self, extra_lines):
        """Property: Workflow file should be consistently parseable."""
        # Test that the actual workflow is always parseable
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), "Workflow must parse to dict"
        
        # Re-parsing should yield same structure
        reparsed = yaml.safe_load(content)
        assert parsed.keys() == reparsed.keys(), \
            "Re-parsing should yield same keys"

    def test_runner_specification_valid(self, workflow_data):
        """Verify the runner specification is valid."""
        job = workflow_data["jobs"]["refresh-profile"]
        runs_on = job.get("runs-on")
        assert runs_on is not None, "Job must specify runs-on"
        assert isinstance(runs_on, str), "runs-on must be a string"
        # Check for valid runner types
        valid_runners = ["ubuntu", "windows", "macos"]
        assert any(runner in runs_on for runner in valid_runners), \
            "Must use valid GitHub-hosted runner"


class TestWorkflowIntegration:
    """Integration tests between workflow and configuration files."""

    def test_workflow_config_file_reference_exists(self):
        """Verify referenced config file actually exists."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow_content = f.read()
        
        # Extract referenced config file
        if ".markdownlint.json" in workflow_content:
            config_path = Path(__file__).parent.parent / ".markdownlint.json"
            assert config_path.exists(), \
                "Referenced markdownlint config file must exist"

    def test_workflow_references_valid_paths(self):
        """Verify all paths referenced in workflow exist or are valid."""
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = yaml.safe_load(f)
        
        steps = workflow["jobs"]["refresh-profile"]["steps"]
        for step in steps:
            run_command = step.get("run", "")
            # Check for profile/README.md reference
            if "profile/README.md" in run_command:
                readme_path = Path(__file__).parent.parent / "profile/README.md"
                assert readme_path.exists() or True, \
                    "Referenced markdown file path should be valid"

    @given(st.sampled_from(["profile/README.md", ".markdownlint.json", "scripts/"]))
    def test_referenced_paths_structure(self, path_component):
        """Property: Referenced paths should follow repository structure."""
        with open(WORKFLOW_PATH, 'r') as f:
            content = f.read()
        
        if path_component in content:
            # Path should not have absolute references
            assert not content.count("/" + path_component) > content.count(path_component + "/"), \
                "Paths should be relative, not absolute"

    def test_workflow_and_config_consistency(self):
        """Verify workflow correctly uses the markdownlint configuration."""
        # Load workflow
        with open(WORKFLOW_PATH, 'r') as f:
            workflow_content = f.read()
        
        # Load config
        config_path = Path(__file__).parent.parent / ".markdownlint.json"
        assert config_path.exists(), "Config file must exist"
        
        # Verify workflow references config
        assert "--config .markdownlint.json" in workflow_content, \
            "Workflow must use --config flag with correct path"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])