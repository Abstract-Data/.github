#!/usr/bin/env python3
"""
Validation script to verify the test suite is properly configured.
"""

import sys
from pathlib import Path

def validate_test_suite():
    """Validate that the test suite is properly set up."""
    errors = []
    warnings = []
    
    test_dir = Path(__file__).parent
    
    # Check test files exist
    expected_files = [
        "test_markdownlint_config.py",
        "test_workflow_config.py",
        "test_integration.py",
        "test_markdown_validation.py",
        "requirements.txt",
        "pytest.ini",
        "README.md",
        "TEST_SUMMARY.md",
        "run_tests.sh"
    ]
    
    for filename in expected_files:
        filepath = test_dir / filename
        if not filepath.exists():
            errors.append(f"Missing file: {filename}")
        else:
            print(f"✓ Found: {filename}")
    
    # Check test files have content
    test_files = [f for f in expected_files if f.startswith("test_") and f.endswith(".py")]
    for filename in test_files:
        filepath = test_dir / filename
        if filepath.exists():
            content = filepath.read_text()
            if "hypothesis" not in content.lower():
                errors.append(f"{filename} does not use Hypothesis")
            if "import pytest" not in content:
                errors.append(f"{filename} does not import pytest")
            if len(content.splitlines()) < 50:
                warnings.append(f"{filename} seems short ({len(content.splitlines())} lines)")
            else:
                print(f"✓ {filename} has {len(content.splitlines())} lines")
    
    # Check requirements.txt has necessary packages
    req_file = test_dir / "requirements.txt"
    if req_file.exists():
        requirements = req_file.read_text()
        required_packages = ["pytest", "hypothesis", "pyyaml"]
        for package in required_packages:
            if package not in requirements.lower():
                errors.append(f"requirements.txt missing {package}")
            else:
                print(f"✓ requirements.txt includes {package}")
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n✅ All validations passed!")
    elif not errors:
        print("\n✅ No errors found (warnings present)")
    else:
        print("\n❌ Validation failed")
        sys.exit(1)
    
    print("\nTest suite is ready to use!")
    print("Run tests with: pytest tests/ -v")

if __name__ == "__main__":
    validate_test_suite()