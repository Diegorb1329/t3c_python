"""
Base provider class for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from openai.types import CompletionUsage

from config import ProviderConfig
from models.taxonomy import TaxonomyResponse
from models.claims import ClaimsResponse, DeduplicationResponse


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig, api_key: str):
        """Initialize the provider with configuration and API key."""
        self.config = config
        self.api_key = api_key
        self.client = None
    
    @abstractmethod
    def initialize_client(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def create_taxonomy(self, system_prompt: str, user_prompt: str) -> TaxonomyResponse:
        """Create taxonomy from comments."""
        pass
    
    @abstractmethod
    def extract_claims(self, system_prompt: str, user_prompt: str) -> ClaimsResponse:
        """Extract claims from a comment."""
        pass
    
    @abstractmethod
    def deduplicate_claims(self, system_prompt: str, user_prompt: str) -> DeduplicationResponse:
        """Deduplicate claims."""
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": self.config.name,
            "model": self.config.model,
            "base_url": self.config.base_url,
            "cost_in_per_10k": self.config.cost_in_per_10k,
            "cost_out_per_10k": self.config.cost_out_per_10k
        }
    
    def calculate_cost(self, usage: CompletionUsage) -> float:
        """Calculate cost based on token usage."""
        input_cost = (usage.prompt_tokens * self.config.cost_in_per_10k) / 10000.0
        output_cost = (usage.completion_tokens * self.config.cost_out_per_10k) / 10000.0
        return input_cost + output_cost
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get standard model parameters."""
        return {
            "model": self.config.model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }
    
    def create_messages(self, system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Create messages array for the LLM."""
        return [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ] 