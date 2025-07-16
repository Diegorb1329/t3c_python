"""
Cost estimation utilities for the T3C pipeline.
"""

from typing import List
from config import Config, ProviderConfig


class CostEstimator:
    """Utility for estimating pipeline costs."""
    
    def __init__(self, provider_config: ProviderConfig):
        """Initialize cost estimator with provider configuration."""
        self.provider_config = provider_config
        self.cost_in_per_10k = provider_config.cost_in_per_10k
        self.cost_out_per_10k = provider_config.cost_out_per_10k
    
    def estimate_total_cost(self, comments: List[str]) -> float:
        """Estimate total cost for processing all comments."""
        step1_cost = self.estimate_step1_cost(comments)
        step2_cost = self.estimate_step2_cost(comments)
        step4_cost = self.estimate_step4_cost(comments)
        
        return step1_cost + step2_cost + step4_cost
    
    def estimate_step1_cost(self, comments: List[str]) -> float:
        """Estimate cost for Step 1: Comments to taxonomy."""
        # Calculate input tokens
        comments_total = sum(len(c) for c in comments)
        from prompts.prompts import SystemPrompts
        
        step1_tokens_in = (
            len(SystemPrompts.SYSTEM_PROMPT) + 
            len(SystemPrompts.COMMENT_TO_TREE_PROMPT) + 
            comments_total
        ) / 4.0
        
        # Output tokens (estimated)
        step1_tokens_out = Config.AVG_TREE_LEN_TOKS
        
        # Calculate cost
        cost_in = (step1_tokens_in * self.cost_in_per_10k) / 10000.0
        cost_out = (step1_tokens_out * self.cost_out_per_10k) / 10000.0
        
        return cost_in + cost_out
    
    def estimate_step2_cost(self, comments: List[str]) -> float:
        """Estimate cost for Step 2: Comments to claims."""
        # Calculate input tokens
        comments_total = sum(len(c) for c in comments)
        from prompts.prompts import SystemPrompts
        
        step2_tokens_in = (
            (comments_total / 4.0) + 
            len(comments) * (
                (len(SystemPrompts.SYSTEM_PROMPT) + len(SystemPrompts.COMMENT_TO_CLAIMS_PROMPT)) / 4.0 + 
                Config.AVG_TREE_LEN_TOKS
            )
        )
        
        # Output tokens (estimated)
        step2_tokens_out = len(comments) * Config.AVG_CLAIM_TOKS_OUT
        
        # Calculate cost
        cost_in = (step2_tokens_in * self.cost_in_per_10k) / 10000.0
        cost_out = (step2_tokens_out * self.cost_out_per_10k) / 10000.0
        
        return cost_in + cost_out
    
    def estimate_step4_cost(self, comments: List[str]) -> float:
        """Estimate cost for Step 4: Deduplication."""
        # Calculate input tokens
        from prompts.prompts import SystemPrompts
        
        step4_tokens_in = (
            (len(SystemPrompts.SYSTEM_PROMPT) + len(SystemPrompts.DEDUP_PROMPT)) / 4.0
        ) * (len(comments) ** 0.33) * Config.AVG_DEDUP_INPUT_TOK
        
        # Output tokens (estimated)
        step4_tokens_out = len(comments) * Config.AVG_DEDUPED_CLAIMS_FACTOR
        
        # Calculate cost
        cost_in = (step4_tokens_in * self.cost_in_per_10k) / 10000.0
        cost_out = (step4_tokens_out * self.cost_out_per_10k) / 10000.0
        
        return cost_in + cost_out
    
    def get_cost_breakdown(self, comments: List[str]) -> dict:
        """Get detailed cost breakdown."""
        step1_cost = self.estimate_step1_cost(comments)
        step2_cost = self.estimate_step2_cost(comments)
        step4_cost = self.estimate_step4_cost(comments)
        total_cost = step1_cost + step2_cost + step4_cost
        
        return {
            "step1_taxonomy": round(step1_cost, 4),
            "step2_claims": round(step2_cost, 4),
            "step4_deduplication": round(step4_cost, 4),
            "total": round(total_cost, 4),
            "provider": self.provider_config.name,
            "model": self.provider_config.model
        }
    
    def compare_providers(self, comments: List[str]) -> dict:
        """Compare costs across all providers."""
        comparison = {}
        
        for provider_key in Config.PROVIDERS:
            provider_config = Config.get_provider_config(provider_key)
            estimator = CostEstimator(provider_config)
            cost = estimator.estimate_total_cost(comments)
            comparison[provider_key] = {
                "name": provider_config.name,
                "cost": round(cost, 4),
                "model": provider_config.model
            }
        
        return comparison 