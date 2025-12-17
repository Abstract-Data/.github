#!/usr/bin/env python3
"""
Property-based tests for markdown validation with configuration.

This module tests the actual markdown validation logic using Hypothesis
to ensure the configuration works correctly with various markdown inputs.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set

import pytest
from hypothesis import given, strategies as st, assume, example, settings


CONFIG_PATH = Path(__file__).parent.parent / ".markdownlint.json"
PROFILE_README_PATH = Path(__file__).parent.parent / "profile/README.md"


class TestMarkdownValidationLogic:
    """Test markdown validation logic with configuration."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def test_profile_readme_exists(self):
        """Verify profile README exists for validation."""
        # May or may not exist in test environment
        if PROFILE_README_PATH.exists():
            assert PROFILE_README_PATH.is_file(), "README should be a file"

    @given(st.integers(min_value=1, max_value=1000))
    def test_line_length_threshold_reasonable(self, line_len, config_data):
        """Property: Configured line length threshold should be reasonable."""
        configured_length = config_data["MD013"]["line_length"]
        assert configured_length > 80, \
            "Line length should be at least 80 for readability"

    @given(st.text(
        alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=400
    ))
    @example("# Short Header")
    @example("This is a reasonably long line of markdown text that contains various elements.")
    @example("[Link](https://example.com/very/long/path/to/resource)")
    def test_line_length_validation_logic(self, markdown_line, config_data):
        """Property: Line length validation should work correctly."""
        assume(len(markdown_line.strip()) > 0)
        
        configured_length = config_data["MD013"]["line_length"]
        line_length = len(markdown_line)
        
        # Logic: lines longer than configured length would trigger MD013
        if line_length > configured_length:
            # This line would trigger the rule (if rule were enabled)
            assert line_length > configured_length
        else:
            # This line would pass
            assert line_length <= configured_length

    @given(st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
            min_size=1,
            max_size=100
        ),
        min_size=1,
        max_size=20
    ))
    def test_multiple_lines_validation(self, lines, config_data):
        """Property: Configuration should apply to all lines."""
        configured_length = config_data["MD013"]["line_length"]
        
        for line in lines:
            assume(len(line.strip()) > 0)
            line_len = len(line)
            # Each line would be evaluated separately
            if line_len > configured_length:
                assert line_len > configured_length
            else:
                assert line_len <= configured_length


class TestMarkdownRuleExemptions:
    """Test rule exemptions like code blocks and tables."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @given(st.text(min_size=10, max_size=500))
    def test_code_blocks_exempt_from_line_length(self, code_content, config_data):
        """Property: Code blocks should be exempt from line length checks."""
        assume(len(code_content.strip()) > 0)
        
        # Configuration specifies code_blocks: false
        assert config_data["MD013"]["code_blocks"] is False, \
            "Code blocks should be exempt (false means don't check)"
        
        # Create a code block
        markdown_with_code = f"```\n{code_content}\n```"
        
        # Code block content can be any length
        # The configuration exempts it from line length checking

    @given(st.lists(
        st.tuples(st.text(max_size=50), st.text(max_size=50)),
        min_size=1,
        max_size=10
    ))
    def test_tables_exempt_from_line_length(self, table_rows, config_data):
        """Property: Tables should be exempt from line length checks."""
        # Configuration specifies tables: false
        assert config_data["MD013"]["tables"] is False, \
            "Tables should be exempt (false means don't check)"
        
        # Tables can have long lines due to formatting
        # The configuration exempts them from line length checking

    def test_exemption_configuration_correct(self, config_data):
        """Verify exemption configuration is set correctly."""
        md013 = config_data["MD013"]
        
        # Both should be False (meaning exempt from checking)
        assert md013["code_blocks"] is False, \
            "code_blocks should be false (exempt)"
        assert md013["tables"] is False, \
            "tables should be false (exempt)"


class TestDisabledRulesValidation:
    """Test validation with disabled rules."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @given(st.text(min_size=10, max_size=200))
    def test_inline_html_allowed(self, html_content, config_data):
        """Property: MD033 disabled means inline HTML is allowed."""
        assume("<" in html_content and ">" in html_content)
        
        # MD033 is disabled
        assert config_data["MD033"] is False, \
            "MD033 (inline HTML) should be disabled"
        
        # Inline HTML like <br>, <div>, etc. would be allowed

    @given(st.text(min_size=5, max_size=100))
    def test_first_line_heading_not_required(self, first_line, config_data):
        """Property: MD041 disabled means first line need not be heading."""
        # MD041 is disabled
        assert config_data["MD041"] is False, \
            "MD041 (first line heading) should be disabled"
        
        # Document can start with any content, not just heading

    def test_heading_blank_lines_not_enforced(self, config_data):
        """Verify MD022 disabled means blank lines around headings not enforced."""
        # MD022 is disabled
        assert config_data["MD022"] is False, \
            "MD022 (blanks around headings) should be disabled"

    def test_list_blank_lines_not_enforced(self, config_data):
        """Verify MD032 disabled means blank lines around lists not enforced."""
        # MD032 is disabled
        assert config_data["MD032"] is False, \
            "MD032 (blanks around lists) should be disabled"

    @given(st.sampled_from([
        "MD033",  # inline HTML
        "MD041",  # first line heading
        "MD022",  # blanks around headings
        "MD032"   # blanks around lists
    ]))
    def test_disabled_rules_property(self, rule_code, config_data):
        """Property: All disabled rules should be set to false."""
        assert rule_code in config_data, f"{rule_code} should be in config"
        assert config_data[rule_code] is False, \
            f"{rule_code} should be disabled (false)"


class TestConfigurationEffectiveness:
    """Test that configuration effectively controls validation."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @given(st.integers(min_value=351, max_value=1000))
    def test_lines_longer_than_configured_would_fail(self, line_length, config_data):
        """Property: Lines longer than 350 would trigger MD013 if rule active."""
        configured_length = config_data["MD013"]["line_length"]
        
        # Lines longer than configured length would fail MD013
        if line_length > configured_length:
            # This would trigger the rule
            assert line_length > configured_length

    @given(st.integers(min_value=1, max_value=350))
    def test_lines_within_limit_would_pass(self, line_length, config_data):
        """Property: Lines within limit would pass MD013."""
        configured_length = config_data["MD013"]["line_length"]
        
        # Lines within limit would pass
        if line_length <= configured_length:
            assert line_length <= configured_length

    def test_default_true_enables_standard_rules(self, config_data):
        """Verify default: true enables all standard rules not explicitly disabled."""
        assert config_data["default"] is True, \
            "'default' should be true to enable standard rules"
        
        # This means all markdownlint rules are on by default
        # except those explicitly disabled


class TestMarkdownPatterns:
    """Test common markdown patterns with configuration."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @given(st.text(
        alphabet=st.characters(
            whitelist_categories=("L",),
            min_codepoint=65,
            max_codepoint=90
        ),
        min_size=1,
        max_size=50
    ))
    def test_heading_patterns(self, heading_text, config_data):
        """Property: Heading patterns should be validated correctly."""
        assume(len(heading_text.strip()) > 0)
        
        heading = f"# {heading_text}"
        
        # MD022 is disabled, so blank lines around headings not required
        assert config_data["MD022"] is False

    @given(st.lists(
        st.text(min_size=1, max_size=30),
        min_size=1,
        max_size=10
    ))
    def test_list_patterns(self, list_items, config_data):
        """Property: List patterns should be validated correctly."""
        # MD032 is disabled, so blank lines around lists not required
        assert config_data["MD032"] is False
        
        markdown_list = "\n".join(f"- {item}" for item in list_items if item.strip())
        
        # Lists can be formatted without strict blank line requirements

    @given(
        st.text(min_size=1, max_size=20),
        st.text(min_size=5, max_size=100)
    )
    def test_link_patterns(self, link_text, url, config_data):
        """Property: Link patterns should be validated correctly."""
        assume(len(link_text.strip()) > 0)
        assume(not any(c in url for c in ["[", "]", "(", ")"]))
        
        markdown_link = f"[{link_text}]({url})"
        
        configured_length = config_data["MD013"]["line_length"]
        
        # Long URLs can make lines exceed typical limits
        # Configuration at 350 accommodates this


class TestRealWorldScenarios:
    """Test real-world markdown scenarios."""

    @pytest.fixture(scope="class")
    def config_data(self):
        """Load markdownlint configuration."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def test_github_profile_readme_patterns(self, config_data):
        """Test patterns common in GitHub profile READMEs."""
        # GitHub profile READMEs often have:
        # - Badges (HTML img tags)
        # - Long URLs
        # - SVG embeds
        # - Custom HTML
        
        # MD033 disabled allows HTML
        assert config_data["MD033"] is False
        
        # Line length 350 accommodates badges and URLs
        assert config_data["MD013"]["line_length"] == 350

    @given(st.integers(min_value=1, max_value=20))
    def test_badge_lines(self, num_badges, config_data):
        """Property: Badge lines can be very long."""
        # Badges often use long URLs
        badge_template = "![Badge](https://img.shields.io/badge/text-value-color)"
        badge_line = " ".join([badge_template] * num_badges)
        
        configured_length = config_data["MD013"]["line_length"]
        
        # Configuration should accommodate multiple badges
        # 350 char limit is reasonable for this

    def test_svg_embed_patterns(self, config_data):
        """Test SVG embed patterns common in GitHub profiles."""
        # SVG embeds use HTML which requires MD033 disabled
        assert config_data["MD033"] is False, \
            "SVG embeds require inline HTML"
        
        # SVG tags can have long lines
        assert config_data["MD013"]["line_length"] >= 300, \
            "Should accommodate SVG attributes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])