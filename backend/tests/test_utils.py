import json

from app.utils.json_utils import (
    safe_json_loads,
    safe_json_dumps,
    parse_list_field,
    parse_dict_field
)
from app.utils.markdown_utils import escape_markdown


class TestJsonUtils:
    """Test JSON utility functions"""

    def test_safe_json_loads_valid(self):
        """Test loading valid JSON"""
        result = safe_json_loads('["test", "data"]')
        assert result == ["test", "data"]

    def test_safe_json_loads_invalid(self):
        """Test loading invalid JSON returns default"""
        result = safe_json_loads('invalid json', default=[])
        assert result == []

    def test_safe_json_loads_none(self):
        """Test loading None returns default"""
        result = safe_json_loads(None, default=[])
        assert result == []

    def test_safe_json_loads_default_dict(self):
        """Test loading with dict default"""
        result = safe_json_loads('invalid', default={})
        assert result == {}

    def test_safe_json_dumps_valid(self):
        """Test dumping valid data"""
        result = safe_json_dumps({"key": "value"})
        assert json.loads(result) == {"key": "value"}

    def test_safe_json_dumps_with_unicode(self):
        """Test dumping unicode data"""
        result = safe_json_dumps({"key": "тест"}, ensure_ascii=False)
        assert "тест" in result

    def test_parse_list_field_valid(self):
        """Test parsing valid list field"""
        result = parse_list_field('["a", "b", "c"]')
        assert result == ["a", "b", "c"]

    def test_parse_list_field_invalid(self):
        """Test parsing invalid list field"""
        result = parse_list_field('invalid')
        assert result == []

    def test_parse_list_field_none(self):
        """Test parsing None list field"""
        result = parse_list_field(None)
        assert result == []

    def test_parse_dict_field_valid(self):
        """Test parsing valid dict field"""
        result = parse_dict_field('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_dict_field_invalid(self):
        """Test parsing invalid dict field"""
        result = parse_dict_field('invalid')
        assert result == {}

    def test_parse_dict_field_none(self):
        """Test parsing None dict field"""
        result = parse_dict_field(None)
        assert result == {}


class TestMarkdownUtils:
    """Test Markdown utility functions"""

    def test_escape_markdown_basic(self):
        """Test escaping basic special characters"""
        text = "Hello_World"
        result = escape_markdown(text)
        assert result == "Hello\\_World"

    def test_escape_markdown_multiple(self):
        """Test escaping multiple special characters"""
        text = "Test*bold*_italic_"
        result = escape_markdown(text)
        assert result == "Test\\*bold\\*\\_italic\\_"

    def test_escape_markdown_all_chars(self):
        """Test escaping all special characters"""
        text = "_*[]()~`>#+-=|{}.!"
        result = escape_markdown(text)
        assert "\\" in result
        assert all(f"\\{char}" in result for char in text)

    def test_escape_markdown_empty(self):
        """Test escaping empty string"""
        result = escape_markdown("")
        assert result == ""

    def test_escape_markdown_no_special(self):
        """Test text without special characters"""
        text = "Hello World 123"
        result = escape_markdown(text)
        assert result == text

    def test_escape_markdown_with_newlines(self):
        """Test escaping text with newlines"""
        text = "Line1\nLine2_test"
        result = escape_markdown(text)
        assert "\n" in result
        assert "\\_" in result
