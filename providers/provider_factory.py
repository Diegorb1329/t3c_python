"""
Provider factory for creating LLM providers.
"""

from typing import Dict, Type
from providers.base_provider import BaseLLMProvider
from providers.openai_provider import OpenAIProvider
from providers.openrouter_provider import OpenRouterProvider
from config import Config, ProviderConfig


class ProviderFactory:
    """Factory for creating LLM providers."""
    
    # Registry of available providers
    PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
        'openai': OpenAIProvider,
        'openrouter': OpenRouterProvider
    }
    
    @classmethod
    def create_provider(cls, provider_key: str) -> BaseLLMProvider:
        """Create a provider instance based on the provider key."""
        if provider_key not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}. Available providers: {list(cls.PROVIDERS.keys())}")
        
        # Get provider configuration
        provider_config = Config.get_provider_config(provider_key)
        
        # Get API key
        api_key = Config.get_api_key(provider_key)
        
        # Create provider instance
        provider_class = cls.PROVIDERS[provider_key]
        return provider_class(provider_config, api_key)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider keys."""
        return list(cls.PROVIDERS.keys())
    
    @classmethod
    def validate_provider(cls, provider_key: str) -> bool:
        """Validate that a provider is available and configured."""
        if provider_key not in cls.PROVIDERS:
            return False
        
        return Config.validate_environment(provider_key)
    
    @classmethod
    def get_provider_info(cls, provider_key: str) -> Dict[str, str]:
        """Get information about a provider without creating it."""
        if provider_key not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}")
        
        config = Config.get_provider_config(provider_key)
        return {
            "name": config.name,
            "model": config.model,
            "base_url": config.base_url,
            "cost_in_per_10k": config.cost_in_per_10k,
            "cost_out_per_10k": config.cost_out_per_10k
        } 