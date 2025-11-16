"""JSON serialization utilities"""
import json
from typing import Any, List, Dict


def safe_json_loads(data: str | None, default: Any = None) -> Any:
    """
    Safely load JSON data with a default fallback
    
    Args:
        data: JSON string to parse
        default: Default value if parsing fails or data is None
        
    Returns:
        Parsed data or default value
    """
    if data is None:
        return default if default is not None else []
    
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def safe_json_dumps(data: Any, ensure_ascii: bool = False) -> str:
    """
    Safely dump data to JSON string
    
    Args:
        data: Data to serialize
        ensure_ascii: Whether to escape non-ASCII characters
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, ensure_ascii=ensure_ascii)
    except (TypeError, ValueError):
        return json.dumps({})


def parse_list_field(field_value: str | None) -> List:
    """Parse a JSON list field with safe fallback"""
    return safe_json_loads(field_value, default=[])


def parse_dict_field(field_value: str | None) -> Dict:
    """Parse a JSON dict field with safe fallback"""
    return safe_json_loads(field_value, default={})
