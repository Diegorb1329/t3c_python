"""
JSON Schema loader and structured output utilities for T3C pipeline.
"""

import json
import os
from typing import Dict, Any


class JSONSchemaLoader:
    """Utility for loading JSON schemas and handling structured outputs."""
    
    @staticmethod
    def load_schema(schema_name: str) -> Dict[str, Any]:
        """Load a JSON schema from the schemas directory."""
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schemas', f'{schema_name}.json')
        
        with open(schema_path, 'r') as f:
            schema = json.load(f)
        
        return schema
    
    @staticmethod
    def create_structured_response_format(schema_name: str) -> Dict[str, Any]:
        """Create a structured response format for OpenRouter."""
        schema = JSONSchemaLoader.load_schema(schema_name)
        
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema
            }
        }
    
    @staticmethod
    def get_t3c_output_schema() -> Dict[str, Any]:
        """Get the T3C output schema for structured outputs."""
        return JSONSchemaLoader.load_schema("t3c_output_schema")
    
    @staticmethod
    def get_t3c_response_format() -> Dict[str, Any]:
        """Get the T3C response format for structured outputs."""
        return JSONSchemaLoader.create_structured_response_format("t3c_output_schema") 