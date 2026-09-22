"""
Bailian (百炼) Model Provider

Connects to Alibaba Cloud Bailian API for real LLM inference.
"""

import json
import os
from typing import Dict, Any, Optional
import requests


class BailianProvider:
    """
    Provider for Alibaba Cloud Bailian (百炼) models

    Configuration via environment variables:
        BAILIAN_API_URL: API endpoint URL
        BAILIAN_API_KEY: API key for authentication
        BAILIAN_MODEL: Model name (e.g., "qwen-max", "qwen-plus")

    Or pass directly to __init__
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Bailian provider

        Args:
            api_url: API endpoint (or use BAILIAN_API_URL env var)
            api_key: API key (or use BAILIAN_API_KEY env var)
            model: Model name (or use BAILIAN_MODEL env var, default: qwen-plus)
            timeout: Request timeout in seconds
            max_retries: Max retry attempts on failure
        """
        self.api_url = api_url or os.getenv("BAILIAN_API_URL")
        self.api_key = api_key or os.getenv("BAILIAN_API_KEY")
        self.model = model or os.getenv("BAILIAN_MODEL", "qwen-plus")
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_url:
            raise ValueError(
                "Bailian API URL not provided. "
                "Set BAILIAN_API_URL environment variable or pass api_url parameter."
            )

        if not self.api_key:
            raise ValueError(
                "Bailian API key not provided. "
                "Set BAILIAN_API_KEY environment variable or pass api_key parameter."
            )

        self.call_count = 0

    def generate(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate response from Bailian API

        Args:
            prompt: Input prompt
            schema: Optional JSON schema for structured output
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response (parsed JSON if schema provided, else text)

        Raises:
            Exception: If API call fails after retries
        """
        self.call_count += 1

        # Build request payload
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }

        # Add schema guidance if provided
        if schema:
            # Convert Pydantic model to JSON schema if needed
            try:
                from pydantic import BaseModel
                if isinstance(schema, type) and issubclass(schema, BaseModel):
                    schema_dict = schema.model_json_schema()
                else:
                    schema_dict = schema
            except ImportError:
                schema_dict = schema

            # Append schema instruction to prompt
            schema_instruction = f"\n\n请按照以下 JSON schema 格式返回结果：\n{json.dumps(schema_dict, ensure_ascii=False, indent=2)}"
            payload["input"]["messages"][0]["content"] += schema_instruction

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                response.raise_for_status()
                result = response.json()

                # Extract response text
                if "output" in result and "choices" in result["output"]:
                    text = result["output"]["choices"][0]["message"]["content"]
                elif "output" in result and "text" in result["output"]:
                    text = result["output"]["text"]
                else:
                    raise ValueError(f"Unexpected response format: {result}")

                # Parse JSON if schema was provided
                if schema:
                    try:
                        # Try to extract JSON from markdown code blocks
                        if "```json" in text:
                            json_start = text.index("```json") + 7
                            json_end = text.index("```", json_start)
                            text = text[json_start:json_end].strip()
                        elif "```" in text:
                            json_start = text.index("```") + 3
                            json_end = text.index("```", json_start)
                            text = text[json_start:json_end].strip()

                        return json.loads(text)
                    except (json.JSONDecodeError, ValueError) as e:
                        # If JSON parsing fails, return raw text with warning
                        return {
                            "_raw_text": text,
                            "_parse_error": str(e),
                            "_warning": "Failed to parse JSON, returning raw text"
                        }

                return {"text": text}

            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
                    continue
                else:
                    break

        # All retries failed
        raise Exception(f"Bailian API call failed after {self.max_retries} attempts: {last_error}")

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate structured output matching the schema

        Args:
            prompt: Input prompt
            schema: JSON schema for output structure
            temperature: Sampling temperature

        Returns:
            Parsed JSON matching schema
        """
        return self.generate(prompt, schema=schema, temperature=temperature)

    def reset_stats(self):
        """Reset call counter"""
        self.call_count = 0


# Convenience function to create provider from config file
def create_from_config(config_path: str) -> BailianProvider:
    """
    Create BailianProvider from JSON config file

    Config format:
    {
        "api_url": "https://...",
        "api_key": "sk-...",
        "model": "qwen-plus",
        "timeout": 30,
        "max_retries": 3
    }

    Args:
        config_path: Path to JSON config file

    Returns:
        Configured BailianProvider
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return BailianProvider(**config)
