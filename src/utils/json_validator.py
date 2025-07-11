"""JSON validation and correction utilities for healthcare database responses."""

from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError
import json
import re


class JSONResponseValidator:
    """Enhanced JSON validation and correction utilities for healthcare database responses.
    
    This class provides methods to validate, parse, and fix malformed JSON responses
    from database agents, ensuring consistent response formatting.
    """
    
    @staticmethod
    def validate_and_fix_json(response_text: str) -> Dict[str, Any]:
        """Validate and attempt to fix malformed JSON responses.
        
        Args:
            response_text: Raw text response that may contain JSON
            
        Returns:
            Dictionary containing parsed JSON or constructed response
            
        Raises:
            None: Always returns a valid dictionary, constructs one if parsing fails
        """
        
        cleaned_text = response_text.strip()
        if cleaned_text.startswith('{') and cleaned_text.endswith('}'):
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError:
                pass
        
        json_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL | re.IGNORECASE)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                potential_json = match.group()
                return json.loads(potential_json)
            except json.JSONDecodeError:
                continue
        
        return JSONResponseValidator._construct_from_text(response_text)
    
    @staticmethod
    def _construct_from_text(text: str) -> Dict[str, Any]:
        """Construct JSON structure from unstructured text.
        
        When JSON parsing fails, this method analyzes the text content
        to construct a valid response dictionary with inferred values.
        
        Args:
            text: Unstructured text response
            
        Returns:
            Dictionary with standard response structure
        """
        result = {
            "success": False,
            "message": "Unable to parse structured response",
            "query_understanding": "Response parsing failed",
            "sql_query": None,
            "result_count": 0,
            "results": [],
            "metadata": {"constructed_from_text": True}
        }
        
        if "success" in text.lower() or "found" in text.lower():
            result["success"] = True
            result["message"] = "Query appeared to succeed based on text analysis"
        
        sql_match = re.search(r'SELECT.*?(?:;|\n|FROM.*?WHERE.*?;)', text, re.IGNORECASE | re.DOTALL)
        if sql_match:
            result["sql_query"] = sql_match.group().strip()
        
        numbers = re.findall(r'\b(\d+)\b', text)
        if numbers:
            result["result_count"] = int(numbers[0])
        
        sentences = text.split('.')[:2]
        if sentences:
            result["message"] = '. '.join(sentences).strip()
        
        return result