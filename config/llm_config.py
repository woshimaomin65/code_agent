"""LLM Configuration."""
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration settings."""

    api_base: str = Field(
        default="https://api.deepseek.com",
        description="API base URL"
    )
    api_key: str = Field(
        default="",
        description="API key for authentication"
    )
    model: str = Field(
        default="deepseek-chat",
        description="Model name to use"
    )
    response_format: Literal["text", "json"] = Field(
        default="text",
        description="Response format"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens to generate"
    )
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra parameters to pass to the LLM API"
    )
    streaming: bool = Field(
        default=False,
        description="Enable streaming mode for LLM responses"
    )

    @classmethod
    def from_dict(cls, config_dict: dict) -> "LLMConfig":
        """Create config from dictionary."""
        return cls(**config_dict)

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return self.model_dump()
