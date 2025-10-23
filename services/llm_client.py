"""
LLM Client Service

Handles communication with Claude API for voice transformations
"""
import os
from typing import Optional
from anthropic import Anthropic


class LLMClient:
    """Client for Claude API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = Anthropic(api_key=self.api_key)

    def transform_content(
        self,
        prompt: str,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.0
    ) -> str:
        """
        Transform content using Claude

        Args:
            prompt: The transformation prompt with instructions and content
            model: Claude model to use (haiku for speed/cost, sonnet for quality)
            max_tokens: Maximum tokens in response
            temperature: 0.0 for deterministic, higher for creative

        Returns:
            Transformed content
        """
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                return response.content[0].text

            raise ValueError("Empty response from Claude API")

        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")


# Singleton instance
_llm_client = None


def get_llm_client() -> LLMClient:
    """Get or create singleton LLM client"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
