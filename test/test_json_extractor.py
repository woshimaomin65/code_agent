"""Tests for robust JSON extraction utility."""
import pytest
from utils.json_extractor import JSONExtractor


def test_basic_array_extraction():
    """Test basic JSON array extraction."""
    extractor = JSONExtractor()
    text = 'Here is the plan: [{"id": 1, "name": "test"}]'
    result = extractor.extract(text, expect_array=True)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]['id'] == 1


def test_basic_object_extraction():
    """Test basic JSON object extraction."""
    extractor = JSONExtractor()
    text = '{"achieved": true, "reason": "done"}'
    result = extractor.extract(text, expect_array=False)
    assert isinstance(result, dict)
    assert 'achieved' in result


def test_code_block_extraction():
    """Test extraction from markdown code blocks."""
    extractor = JSONExtractor()
    text = """Here is the plan:
```json
[
  {"id": 1, "description": "test"}
]
```
"""
    result = extractor.extract(text, expect_array=True)
    assert isinstance(result, list)
    assert len(result) == 1


def test_trailing_comma_repair():
    """Test repair of trailing commas."""
    extractor = JSONExtractor()
    # This has a trailing comma which is invalid JSON
    text = '[{"id": 1, "name": "test",}]'
    result = extractor.extract(text, expect_array=True)
    assert isinstance(result, list)
    assert len(result) == 1


def test_extraction_with_text_before_and_after():
    """Test extraction when JSON is surrounded by text."""
    extractor = JSONExtractor()
    text = """
    Let me create a plan for you.

    [
      {"id": 1, "description": "First step"},
      {"id": 2, "description": "Second step"}
    ]

    This plan should work well.
    """
    result = extractor.extract(text, expect_array=True)
    assert isinstance(result, list)
    assert len(result) == 2


def test_invalid_json_raises_error():
    """Test that completely invalid JSON raises an error."""
    extractor = JSONExtractor()
    text = "This is not JSON at all"
    with pytest.raises(ValueError):
        extractor.extract(text, expect_array=True)


if __name__ == "__main__":
    # Run basic tests
    test_basic_array_extraction()
    test_basic_object_extraction()
    test_code_block_extraction()
    test_trailing_comma_repair()
    test_extraction_with_text_before_and_after()
    print("✅ All tests passed!")
