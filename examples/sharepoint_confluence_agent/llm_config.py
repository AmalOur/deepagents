"""Custom LLM configuration for Qwen model."""

import os
from typing import Optional
from langchain_openai import ChatOpenAI


def get_custom_llm(
    model_name: Optional[str] = None,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: Optional[int] = 4096,
) -> ChatOpenAI:
    """
    Get a custom LLM instance configured from environment variables.

    This function creates a ChatOpenAI instance that's compatible with any OpenAI-compatible API,
    including the custom Qwen model.

    Environment Variables:
        LLM_MODEL_NAME: Name of the model (e.g., "Qwen/QVQ-72B-Preview")
        LLM_API_BASE: Base URL for the API (e.g., "https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1")
        LLM_API_KEY: API key for authentication

    Args:
        model_name: Override model name from environment
        api_base: Override API base URL from environment
        api_key: Override API key from environment
        temperature: Temperature for generation (default: 0.0 for deterministic output)
        max_tokens: Maximum tokens to generate (default: 4096)

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If required environment variables are not set

    Example:
        # Using environment variables
        llm = get_custom_llm()

        # With overrides
        llm = get_custom_llm(
            model_name="Qwen/QVQ-72B-Preview",
            api_base="https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1",
            api_key="my-key",
        )
    """
    # Get configuration from environment or parameters
    model_name = model_name or os.getenv("LLM_MODEL_NAME")
    api_base = api_base or os.getenv("LLM_API_BASE")
    api_key = api_key or os.getenv("LLM_API_KEY")

    # Validate required parameters
    if not model_name:
        raise ValueError(
            "LLM_MODEL_NAME must be set in environment or passed as parameter. "
            "Example: LLM_MODEL_NAME=Qwen/QVQ-72B-Preview"
        )

    if not api_base:
        raise ValueError(
            "LLM_API_BASE must be set in environment or passed as parameter. "
            "Example: LLM_API_BASE=https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1"
        )

    if not api_key:
        raise ValueError(
            "LLM_API_KEY must be set in environment or passed as parameter. "
            "Example: LLM_API_KEY=my-key"
        )

    # Create ChatOpenAI instance with custom configuration
    # Configure for models that may not support full tool calling
    llm = ChatOpenAI(
        model=model_name,
        openai_api_base=api_base,
        openai_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        # Add custom header for X-API-Key
        default_headers={"X-API-Key": api_key},
        # Disable strict tool calling validation for compatibility
        model_kwargs={
            "tool_choice": "none",  # Don't force tool usage
        }
    )

    return llm


def get_qwen_llm(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> ChatOpenAI:
    """
    Get a Qwen LLM instance specifically configured for the QVQ-72B model.

    This is a convenience function that uses get_custom_llm() with defaults
    suitable for the Qwen QVQ-72B-Preview model.

    Args:
        temperature: Temperature for generation (default: 0.0)
        max_tokens: Maximum tokens to generate (default: 4096)

    Returns:
        Configured ChatOpenAI instance for Qwen

    Example:
        llm = get_qwen_llm()
    """
    return get_custom_llm(temperature=temperature, max_tokens=max_tokens)


class QwenLLMConfig:
    """
    Configuration class for Qwen LLM settings.

    This class provides a structured way to manage LLM configuration
    and can be easily extended for additional settings.

    Example:
        config = QwenLLMConfig(
            model_name="Qwen/QVQ-72B-Preview",
            api_base="https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1",
            api_key="my-key",
            temperature=0.0,
        )
        llm = config.get_llm()
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        streaming: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize LLM configuration.

        Args:
            model_name: Model name (defaults to LLM_MODEL_NAME env var)
            api_base: API base URL (defaults to LLM_API_BASE env var)
            api_key: API key (defaults to LLM_API_KEY env var)
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            streaming: Enable streaming responses
            verbose: Enable verbose logging
        """
        self.model_name = model_name or os.getenv("LLM_MODEL_NAME")
        self.api_base = api_base or os.getenv("LLM_API_BASE")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.streaming = streaming
        self.verbose = verbose

    def get_llm(self) -> ChatOpenAI:
        """
        Get a configured LLM instance.

        Returns:
            Configured ChatOpenAI instance
        """
        return get_custom_llm(
            model_name=self.model_name,
            api_base=self.api_base,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    @classmethod
    def from_env(cls) -> "QwenLLMConfig":
        """
        Create configuration from environment variables.

        Returns:
            QwenLLMConfig instance

        Example:
            config = QwenLLMConfig.from_env()
            llm = config.get_llm()
        """
        return cls()

    def validate(self) -> bool:
        """
        Validate that all required configuration is present.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if not self.model_name:
            raise ValueError("model_name must be set")
        if not self.api_base:
            raise ValueError("api_base must be set")
        if not self.api_key:
            raise ValueError("api_key must be set")
        return True


# Example usage function
def example_usage():
    """
    Example usage of the LLM configuration.

    This function demonstrates how to use the custom LLM with the Qwen model.
    """
    from openai import OpenAI

    # Method 1: Using environment variables
    try:
        llm = get_qwen_llm()
        print("✓ LLM configured successfully from environment variables")
    except ValueError as e:
        print(f"✗ Error: {e}")

    # Method 2: Using explicit parameters
    llm = get_custom_llm(
        model_name="Qwen/QVQ-72B-Preview",
        api_base="https://model-mlqvq-72b-799001-614977.ai.gcore.dev/v1",
        api_key="my-key",
    )

    # Method 3: Using configuration class
    config = QwenLLMConfig.from_env()
    config.validate()
    llm = config.get_llm()

    # Test the LLM
    response = llm.invoke("What is the capital of France?")
    print(f"Response: {response.content}")

    # Using raw OpenAI client (for reference)
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_API_BASE"),
    )

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL_NAME"),
        messages=[
            {"role": "user", "content": "What is the capital of France?"},
        ],
        extra_headers={"X-API-Key": os.getenv("LLM_API_KEY")},
    )
    print(f"Response (raw): {response.choices[0].message.content}")


if __name__ == "__main__":
    # Run example if executed directly
    example_usage()
