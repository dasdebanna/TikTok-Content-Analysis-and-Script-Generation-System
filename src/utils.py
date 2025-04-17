import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

import pandas as pd
from openai import OpenAI

from config.settings import (
    OPENAI_API_KEY, 
    LLM_MODEL, 
    APP_NAME, 
    APP_URL,
    RAW_DATA_DIR, 
    PROCESSED_DATA_DIR
)

logger = logging.getLogger(__name__)

# LLM Client Setup
def setup_llm_client():
    """Set up and return an OpenAI client"""
    return OpenAI(api_key=OPENAI_API_KEY)

def generate_llm_response(prompt: str, system_message: str = None, json_output: bool = False) -> str:
    """Generate a response from the LLM using OpenAI"""
    client = setup_llm_client()
    
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            response_format={"type": "json_object"} if json_output else None,
        )
        response = completion.choices[0].message.content
        
        # If JSON output was requested, try to ensure it's valid JSON
        if json_output:
            try:
                # Try to parse as JSON
                json.loads(response)
                return response
            except json.JSONDecodeError:
                # If not valid JSON, create a simple valid JSON object with the response
                logger.warning("LLM did not return valid JSON. Creating fallback structure.")
                return json.dumps({
                    "content_type": "unknown",
                    "content_approach": "unknown", 
                    "reasoning": "Model did not return valid JSON",
                    "original_response": response
                })
        return response
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        if json_output:
            return json.dumps({"error": str(e)})
        return f"Error: {str(e)}"

def get_timestamp_str() -> str:
    """Get a string timestamp in the format YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def load_json(filepath: str) -> Dict:
    """Load data from a JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading data from {filepath}: {e}")
        raise

def save_json(data: Any, filepath: str) -> None:
    """Save data to a JSON file with custom serialization for problematic types"""
    try:
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                # Handle pandas Timestamp objects
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                # Handle numpy types
                if hasattr(obj, 'item'):
                    return obj.item()
                # Handle sets
                if isinstance(obj, set):
                    return list(obj)
                # Let the base class handle everything else
                try:
                    return json.JSONEncoder.default(self, obj)
                except TypeError:
                    return str(obj)  # Convert to string as fallback
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, cls=CustomEncoder)
        logger.info(f"Data saved to {filepath}")
    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")