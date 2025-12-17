# Test Suite for Abstract Data Organization Profile

This directory contains comprehensive property-based and stateful tests for the Abstract Data organization profile repository, using [Hypothesis](https://hypothesis.readthedocs.io/) for advanced property-based testing.

## Overview

The test suite validates configuration files and workflow definitions through:

- **Property-based testing**: Validates properties that should hold true across a wide range of inputs
- **Stateful testing**: Uses state machines to test complex behavioral properties
- **Integration testing**: Ensures components work together correctly
- **Edge case testing**: Validates behavior under unusual or boundary conditions

## Test Files

### `test_markdownlint_config.py`

Comprehensive tests for `.markdownlint.json` configuration file:

- **Structure validation**: Ensures config has required fields and valid structure
- **Property tests**: Validates configuration properties across various scenarios
- **Stateful tests**: Uses state machine to verify configuration consistency
- **Edge cases**: Tests boundary conditions and error handling
- **Integration**: Verifies config works with workflow

**Key test classes:**
- `TestMarkdownlintConfigStructure`: Basic structure and validation
- `TestMarkdownlintConfigProperties`: Property-based tests with Hypothesis
- `TestMarkdownlintConfigCompatibility`: Compatibility and serialization tests
- `MarkdownlintConfigStateMachine`: Stateful testing with state machine
- `TestMarkdownlintConfigEdgeCases`: Edge cases and error conditions
- `TestMarkdownlintConfigIntegration`: Integration with workflow

### `test_workflow_config.py`

Comprehensive tests for `.github/workflows/update-profile.yml`:

- **Workflow structure**: Validates YAML structure and required fields
- **Step validation**: Ensures all steps are properly configured
- **Command validation**: Verifies markdownlint command uses correct flags
- **Step ordering**: Validates logical step dependencies
- **Property tests**: Tests workflow properties across scenarios
- **Stateful tests**: State machine validation of workflow configuration
- **Integration**: Validates workflow references to config files

**Key test classes:**
- `TestWorkflowStructure`: Basic workflow structure validation
- `TestWorkflowMarkdownlintStep`: Specific validation of markdownlint step
- `TestWorkflowStepOrdering`: Validates step order and dependencies
- `TestWorkflowProperties`: Property-based tests
- `WorkflowConfigStateMachine`: Stateful testing with state machine
- `TestWorkflowEdgeCases`: Edge cases and failure conditions
- `TestWorkflowIntegration`: Integration between workflow and configs

## Installation

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

## Running Tests

Run all tests:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_markdownlint_config.py -v
```

Run with Hypothesis statistics:
```bash
pytest tests/ --hypothesis-show-statistics
```

Run only property-based tests:
```bash
pytest tests/ -m property
```

Run only stateful tests:
```bash
pytest tests/ -m stateful
```

Run with increased Hypothesis examples:
```bash
pytest tests/ --hypothesis-seed=12345
```

## Test Coverage

The test suite covers:

### Markdownlint Configuration (`.markdownlint.json`)

✅ **Structure validation**
- Valid JSON format
- Required fields present
- Correct data types

✅ **Rule configuration**
- MD013 (line length) validation
- Disabled rules (MD033, MD041, MD022, MD032)
- Boolean properties

✅ **Property-based tests**
- Line length bounds checking
- Rule name format validation
- Boolean property validation
- JSON serialization round-trip

✅ **Stateful tests**
- Configuration consistency across state transitions
- Invariant checking
- Rule persistence validation

✅ **Edge cases**
- Empty content handling
- Minimum required fields
- Schema compatibility
- Comparison operations

✅ **Integration**
- Workflow reference validation
- Path correctness
- Content validation with various inputs

### Workflow Configuration (`.github/workflows/update-profile.yml`)

✅ **Structure validation**
- Valid YAML format
- Required GitHub Actions keys
- Job structure validation

✅ **Markdownlint step**
- Config flag usage
- Config file reference
- Target file validation
- Command structure

✅ **Step ordering**
- Checkout first
- Node.js setup before npm commands
- Validation before commit

✅ **Property-based tests**
- Sufficient step count
- Required fields in all steps
- Descriptive step names
- Expected keywords present

✅ **Stateful tests**
- Workflow structure consistency
- Step analysis across indices
- Environment variable validation
- Invariant checking

✅ **Edge cases**
- Secrets reference handling
- No hardcoded credentials
- Error handling structure
- Parser stability
- Valid runner specification

✅ **Integration**
- Config file existence
- Valid path references
- Consistent configuration usage

## Hypothesis Testing Strategy

### Property-Based Testing

Tests validate properties that should always hold true:

```python
@given(st.integers(min_value=1, max_value=10000))
def test_line_length_property_positive_values(self, line_length):
    """Property: Line length must always be positive when valid."""
    ...
```

### Stateful Testing

State machines test complex behavioral properties:

```python
class MarkdownlintConfigStateMachine(RuleBasedStateMachine):
    @rule()
    def verify_config_structure(self):
        """Rule: Configuration structure should always be valid."""
        ...
    
    @invariant()
    def config_is_valid_json_structure(self):
        """Invariant: Config should always be a valid dictionary."""
        ...
```

## Test Design Principles

1. **Comprehensive Coverage**: Tests cover happy paths, edge cases, and failure conditions
2. **Property-Based**: Uses Hypothesis to generate diverse test inputs
3. **Stateful Validation**: State machines verify complex behavioral properties
4. **Integration Focus**: Validates components work together correctly
5. **Clear Naming**: Test names clearly describe what they validate
6. **Maintainable**: Tests follow project conventions and best practices

## Adding New Tests

When adding new tests:

1. Follow existing naming conventions (`test_*`)
2. Use Hypothesis for property-based tests when possible
3. Add appropriate markers (`@pytest.mark.property`, etc.)
4. Document what property or invariant is being tested
5. Ensure tests are independent and can run in any order
6. Use fixtures for shared test data

Example:

```python
@given(st.text(min_size=1, max_size=100))
def test_new_property(self, test_input):
    """Property: Describe the property being tested."""
    # Test implementation
    assert property_holds(test_input)
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

- Fast execution with reasonable Hypothesis example counts
- Clear failure messages
- No external dependencies required
- Deterministic when needed (via seeds)

## Troubleshooting

**Tests fail with Hypothesis health check warnings:**
```bash
pytest tests/ --hypothesis-suppress-health-check=all
```

**Need more examples for debugging:**
```bash
pytest tests/ --hypothesis-verbosity=verbose
```

**Flaky test detection:**
```bash
pytest tests/ --hypothesis-seed=random
```

## Contributing

When contributing tests:

1. Ensure all tests pass locally
2. Add tests for new features or bug fixes
3. Use Hypothesis strategies effectively
4. Document complex test logic
5. Follow the existing test structure

## License

These tests are part of the Abstract Data organization profile repository.