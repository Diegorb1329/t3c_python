"""
OpenRouter provider implementation.
"""

import json
from openai import OpenAI
from typing import Dict, Any

from providers.base_provider import BaseLLMProvider
from config import ProviderConfig, Config
from models.taxonomy import TaxonomyResponse
from models.claims import ClaimsResponse, DeduplicationResponse


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider implementation."""
    
    def __init__(self, config: ProviderConfig, api_key: str):
        """Initialize OpenRouter provider."""
        super().__init__(config, api_key)
        self.initialize_client()
    
    def initialize_client(self) -> None:
        """Initialize OpenRouter client."""
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.config.base_url,
            default_headers=Config.OPENROUTER_HEADERS
        )
        print(f"🔗 Connected to OpenRouter with Gemini 2.0 Flash")
    
    def create_taxonomy(self, system_prompt: str, user_prompt: str) -> TaxonomyResponse:
        """Create taxonomy from comments using OpenRouter."""
        messages = self.create_messages(system_prompt, user_prompt)
        
        response = self.client.chat.completions.create(
            messages=messages,
            **self.get_model_parameters()
        )
        
        taxonomy_dict = json.loads(response.choices[0].message.content)
        return TaxonomyResponse.from_llm_response(taxonomy_dict, response.usage)
    
    def extract_claims(self, system_prompt: str, user_prompt: str) -> ClaimsResponse:
        """Extract claims from a comment using OpenRouter."""
        messages = self.create_messages(system_prompt, user_prompt)
        
        response = self.client.chat.completions.create(
            messages=messages,
            **self.get_model_parameters()
        )
        
        claims_dict = json.loads(response.choices[0].message.content)
        return ClaimsResponse.from_llm_response(claims_dict, response.usage)
    
    def deduplicate_claims(self, system_prompt: str, user_prompt: str) -> DeduplicationResponse:
        """Deduplicate claims using OpenRouter."""
        messages = self.create_messages(system_prompt, user_prompt)
        
        response = self.client.chat.completions.create(
            messages=messages,
            **self.get_model_parameters()
        )
        
        dedup_dict = json.loads(response.choices[0].message.content)
        return DeduplicationResponse.from_llm_response(dedup_dict, response.usage) 