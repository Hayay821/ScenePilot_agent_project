"""
DashScope Provider for Bailian (百炼) API

Connects agents to Alibaba Cloud's DashScope API for real model inference.
"""

import os
import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

try:
    import dashscope
    from dashscope import Generation
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False


class DashScopeProvider:
    """
    Provider for Alibaba Cloud DashScope (百炼) API

    Supports structured output using JSON schema.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "qwen-max",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize DashScope provider

        Args:
            api_key: DashScope API key (or set DASHSCOPE_API_KEY env var)
            model_name: Model to use (qwen-max, qwen-plus, qwen-turbo)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        if not DASHSCOPE_AVAILABLE:
            raise ImportError(
                "dashscope package not installed. "
                "Install with: pip install dashscope"
            )

        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DashScope API key required. "
                "Set DASHSCOPE_API_KEY environment variable or pass api_key parameter."
            )

        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Configure dashscope
        dashscope.api_key = self.api_key

    def call(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Call DashScope API with structured output

        Args:
            prompt: Input prompt
            schema: Pydantic model for output validation
            temperature: Sampling temperature (0.0 - 2.0)
            top_p: Nucleus sampling parameter

        Returns:
            Parsed response matching schema
        """
        # Build system message with schema if provided
        messages = []

        if schema:
            schema_json = schema.model_json_schema()
            system_prompt = (
                "You are a helpful assistant that outputs valid JSON. "
                f"Your output must match this JSON schema:\n\n"
                f"```json\n{json.dumps(schema_json, indent=2, ensure_ascii=False)}\n```\n\n"
                "Respond with ONLY valid JSON, no other text."
            )
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        # Call API
        response = Generation.call(
            model=self.model_name,
            messages=messages,
            result_format="message",
            temperature=temperature,
            top_p=top_p,
            max_tokens=2000
        )

        # Check for errors
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope API error: {response.code} - {response.message}"
            )

        # Extract response text
        response_text = response.output.choices[0].message.content

        # Parse JSON if schema provided
        if schema:
            try:
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()

                # Parse and validate
                data = json.loads(response_text)
                validated = schema(**data)
                return validated.model_dump()

            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse JSON response: {e}\n"
                    f"Response: {response_text}"
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to validate response against schema: {e}\n"
                    f"Response: {response_text}"
                )

        # Return raw text if no schema
        return {"text": response_text}

    def call_with_retry(
        self,
        prompt: str,
        schema: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call API with automatic retry on failure

        Args:
            prompt: Input prompt
            schema: Pydantic model for output validation
            **kwargs: Additional arguments passed to call()

        Returns:
            Parsed response
        """
        import time

        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self.call(prompt, schema, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    time.sleep(wait_time)

        raise RuntimeError(
            f"Failed after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )


# Example usage
if __name__ == "__main__":
    from pydantic import BaseModel
    from typing import List

    # Example schema
    class ShotPlan(BaseModel):
        creative_goal: str
        priorities: List[str]
        recommended_shots: List[str]

    # Initialize provider
    provider = DashScopeProvider(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        model_name="qwen-max"
    )

    # Test call
    prompt = """
    用户想拍摄一组自然的个人肖像照片用作社交媒体头像。
    请生成一个拍摄计划。
    """

    try:
        result = provider.call_with_retry(prompt, schema=ShotPlan)
        print("✓ API call successful!")
        print(f"Creative Goal: {result['creative_goal']}")
        print(f"Priorities: {', '.join(result['priorities'])}")
        print(f"Shots: {', '.join(result['recommended_shots'])}")
    except Exception as e:
        print(f"❌ Error: {e}")
