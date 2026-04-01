"""Perplexity API integration with Pydantic-AI."""

import os
from typing import Any, Type, TypeVar

from pydantic_ai import Agent, ModelRetry
from pydantic import BaseModel, ConfigDict

from hr_breaker.config import get_settings

T = TypeVar('T', bound=BaseModel)


def create_perplexity_agent(
    model: str,
    result_type: Type[T],
    system_prompt: str | None = None,
) -> Agent[Any, T]:
    """Create a Pydantic-AI Agent using Perplexity API via OpenAI-compatible endpoint.
    
    Args:
        model: Model name (e.g., 'sonar-pro', 'sonar')
        result_type: Pydantic model for structured output
        system_prompt: System prompt for the agent
        
    Returns:
        Configured Agent instance
    """
    settings = get_settings()
    
    # Set environment variables for OpenAI-compatible Perplexity endpoint
    # This configures the OpenAI client used by Pydantic-AI internally
    os.environ['OPENAI_API_KEY'] = settings.perplexity_api_key
    os.environ['OPENAI_BASE_URL'] = 'https://api.perplexity.ai'
    
    # Create agent using openai model string
    # sonar-pro model supports tool calling via Perplexity API
    # Use allow_population_by_field_name=True to handle flexible field naming
    agent = Agent(
        model=f'openai:{model}',
        output_type=result_type,
        system_prompt=system_prompt,
    )
    
    return agent
