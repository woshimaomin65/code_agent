"""Utility for robust JSON extraction from LLM responses."""
import json
import re
import logging
from typing import List, Dict, Any, Union, Optional


class JSONExtractor:
    """Robust JSON extractor with multiple strategies and repair logic."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize JSON extractor."""
        self.logger = logger or logging.getLogger(__name__)

    def extract(self, text: str, expect_array: bool = True) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Extract JSON from LLM response with robust error handling.

        Args:
            text: The text containing JSON
            expect_array: If True, expect a JSON array; if False, expect an object

        Returns:
            Parsed JSON (list or dict depending on expect_array)

        Raises:
            ValueError: If JSON extraction fails after all strategies
        """
        # Try multiple extraction strategies
        strategies = [
            self._extract_basic,
            self._extract_code_block,
            self._extract_with_repair
        ]

        last_error = None
        for strategy in strategies:
            try:
                result = strategy(text, expect_array)
                if result is not None and self._validate_structure(result, expect_array):
                    return result
            except Exception as e:
                last_error = e
                self.logger.debug(f"Strategy {strategy.__name__} failed: {e}")
                continue

        # All strategies failed
        error_msg = f"Failed to extract valid JSON from response. Last error: {last_error}"
        self.logger.error(error_msg)
        self.logger.debug(f"Response text: {text[:500]}...")
        raise ValueError(error_msg)

    def _extract_basic(self, text: str, expect_array: bool) -> Union[List, Dict]:
        """Basic JSON extraction - find first bracket to last bracket."""
        if expect_array:
            start = text.find('[')
            end = text.rfind(']') + 1
        else:
            start = text.find('{')
            end = text.rfind('}') + 1

        if start == -1 or end == 0:
            raise ValueError(f"No JSON {'array' if expect_array else 'object'} found")

        json_str = text[start:end]
        return json.loads(json_str)

    def _extract_code_block(self, text: str, expect_array: bool) -> Union[List, Dict]:
        """Extract JSON from markdown code blocks."""
        bracket = '[' if expect_array else '{'
        closing = ']' if expect_array else '}'

        # Try to find JSON in code blocks (```json ... ``` or ``` ... ```)
        patterns = [
            rf'```json\s*(\{bracket}.*?\{closing})\s*```',
            rf'```\s*(\{bracket}.*?\{closing})\s*```'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)

        raise ValueError("No JSON found in code blocks")

    def _extract_with_repair(self, text: str, expect_array: bool) -> Union[List, Dict]:
        """Extract JSON and attempt to repair common issues."""
        if expect_array:
            start = text.find('[')
            end = text.rfind(']') + 1
        else:
            start = text.find('{')
            end = text.rfind('}') + 1

        if start == -1 or end == 0:
            raise ValueError(f"No JSON {'array' if expect_array else 'object'} found")

        json_str = text[start:end]

        # Try to repair common JSON issues
        repaired = self._repair_json(json_str)
        return json.loads(repaired)

    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair common JSON formatting issues."""
        # Remove trailing commas before ] or }
        repaired = re.sub(r',(\s*[}\]])', r'\1', json_str)

        # Fix missing commas between objects (heuristic)
        repaired = re.sub(r'}\s*{', r'},{', repaired)

        # Remove comments (// or /* */)
        repaired = re.sub(r'//.*?$', '', repaired, flags=re.MULTILINE)
        repaired = re.sub(r'/\*.*?\*/', '', repaired, flags=re.DOTALL)

        # Remove any non-JSON text before first bracket
        if repaired.strip().startswith('[') or repaired.strip().startswith('{'):
            repaired = repaired.strip()

        return repaired

    def _validate_structure(self, data: Union[List, Dict], expect_array: bool) -> bool:
        """Validate that the parsed JSON has the expected structure."""
        if expect_array:
            if not isinstance(data, list):
                return False
            if len(data) == 0:
                return False
        else:
            if not isinstance(data, dict):
                return False

        return True
