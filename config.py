"""
Configuration settings for the T3C Python pipeline.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""
    name: str
    model: str
    base_url: str
    cost_in_per_10k: float
    cost_out_per_10k: float
    env_var_name: str
    api_key_prefix: str


class Config:
    """Main configuration class for the T3C pipeline."""
    
    # Provider configurations
    PROVIDERS = {
        'openai': ProviderConfig(
            name="OpenAI",
            model="gpt-4-turbo-preview",
            base_url="https://api.openai.com/v1",
            cost_in_per_10k=0.1,   # $10 per 1M input tokens
            cost_out_per_10k=0.3,  # $30 per 1M output tokens
            env_var_name="OPENAI_API_KEY",
            api_key_prefix="sk-"
        ),
        'openrouter': ProviderConfig(
            name="OpenRouter (Gemini 2.0 Flash)",
            model="google/gemini-2.0-flash-001",
            base_url="https://openrouter.ai/api/v1",
            cost_in_per_10k=0.0075,  # $0.075 per 1M input tokens
            cost_out_per_10k=0.03,   # $0.30 per 1M output tokens
            env_var_name="OPENROUTER_API_KEY",
            api_key_prefix="sk-or-"
        )
    }
    
    # Default provider
    DEFAULT_PROVIDER = 'openrouter'
    
    # W&B Configuration
    WB_PROJECT_NAME = "deepgov_pipeline_enhanced"
    DEFAULT_EXP_GROUP = "provider_comparison"
    
    # Pipeline estimation constants
    AVG_TREE_LEN_TOKS = 614
    AVG_CLAIM_TOKS_OUT = 130
    AVG_TOPIC_COUNT = 12
    AVG_DEDUP_INPUT_TOK = 12
    AVG_DEDUPED_CLAIMS_FACTOR = 0.6
    
    # OpenRouter specific headers
    OPENROUTER_HEADERS = {
        "HTTP-Referer": "https://deepgov.ai",
        "X-Title": "DeepGov LLM Pipeline"
    }
    
    # Model parameters
    MODEL_TEMPERATURE = 0.0
    RESPONSE_FORMAT = {"type": "json_object"}
    
    @classmethod
    def get_provider_config(cls, provider_key: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        if provider_key not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}. Available: {list(cls.PROVIDERS.keys())}")
        return cls.PROVIDERS[provider_key]
    
    @classmethod
    def get_api_key(cls, provider_key: str) -> str:
        """Get API key for a specific provider."""
        config = cls.get_provider_config(provider_key)
        api_key = os.getenv(config.env_var_name)
        if not api_key:
            raise ValueError(f"API key not found in environment variable: {config.env_var_name}")
        if not api_key.startswith(config.api_key_prefix):
            raise ValueError(f"Invalid API key format for {config.name}")
        return api_key
    
    @classmethod
    def validate_environment(cls, provider_key: str) -> bool:
        """Validate that all required environment variables are set."""
        try:
            cls.get_api_key(provider_key)
            return True
        except ValueError:
            return False


# Runtime configuration that can be modified
class RuntimeConfig:
    """Runtime configuration that can be modified during execution."""
    
    def __init__(self):
        self.provider_key = Config.DEFAULT_PROVIDER
        self.run_name = None
        self.exp_group = Config.DEFAULT_EXP_GROUP
        self.enable_wandb = True
        self.enable_weave = True
        self.debug_mode = False
        
    def set_provider(self, provider_key: str):
        """Set the provider to use."""
        if provider_key not in Config.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_key}")
        self.provider_key = provider_key
        
    def get_current_provider_config(self) -> ProviderConfig:
        """Get current provider configuration."""
        return Config.get_provider_config(self.provider_key)
        
    def get_run_config(self) -> Dict[str, Any]:
        """Get configuration for W&B run."""
        provider_config = self.get_current_provider_config()
        return {
            "model": provider_config.model,
            "provider": provider_config.name,
            "use_openrouter": self.provider_key == 'openrouter',
            "base_url": provider_config.base_url,
            "$_in_10K": provider_config.cost_in_per_10k,
            "$_out_10K": provider_config.cost_out_per_10k,
        } 