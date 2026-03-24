# Quick Start Guide

## Install and Run Tests in 30 Seconds

```bash
# 1. Install dependencies
pip install -r tests/requirements.txt

# 2. Run all tests
pytest tests/ -v

# 3. See Hypothesis statistics
pytest tests/ --hypothesis-show-statistics
```

## What Gets Tested

✅ `.markdownlint.json` - Configuration file structure and rules
✅ `.github/workflows/update-profile.yml` - Workflow configuration
✅ Integration between config and workflow
✅ Markdown validation logic

## Test Results You'll See

- 150+ test methods executed
- Property-based tests with Hypothesis
- Stateful tests with state machines
- Edge cases and failure conditions
- All tests use Hypothesis as required

## Quick Commands

```bash
# Run specific test file
pytest tests/test_markdownlint_config.py -v

# Run with more detail
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Run only property tests
pytest tests/ -k "property"
```

## Need Help?

- Read `tests/README.md` for detailed documentation
- Check `tests/TEST_SUMMARY.md` for complete test coverage
- See `TESTING_GUIDE.md` for comprehensive guide