#!/bin/bash
# Test runner script for Abstract Data organization profile tests

set -e

echo "=========================================="
echo "Abstract Data Profile Test Suite"
echo "=========================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing test dependencies..."
    pip install -r tests/requirements.txt
fi

echo "Running all tests..."
echo ""

# Run tests with various configurations
pytest tests/ \
    -v \
    --tb=short \
    --hypothesis-show-statistics \
    "$@"

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo "All tests completed successfully!"