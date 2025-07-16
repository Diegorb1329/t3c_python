"""
Step 1: Comments to Taxonomy
Given all comments, create a taxonomy/tree of general themes + their nested topics.
"""

import weave
from typing import List, Dict, Any

from providers.base_provider import BaseLLMProvider
from prompts.prompts import SystemPrompts
from models.taxonomy import TaxonomyResponse, Taxonomy
from utils.formatting import Formatter
from utils.logging_utils import Logger


class TaxonomyCreator:
    """Step 1: Create taxonomy from comments."""
    
    def __init__(self, provider: BaseLLMProvider, logger: Logger):
        """Initialize taxonomy creator."""
        self.provider = provider
        self.logger = logger
    
    @weave.op()
    def create_taxonomy(self, comments: List[str]) -> TaxonomyResponse:
        """Create taxonomy from comments using the LLM provider."""
        
        # Create prompts
        system_prompt = SystemPrompts.SYSTEM_PROMPT
        user_prompt = SystemPrompts.get_taxonomy_prompt(comments)
        
        # Call LLM provider
        response = self.provider.create_taxonomy(system_prompt, user_prompt)
        
        return response
    
    def execute(self, comments: List[str]) -> Dict[str, Any]:
        """Execute Step 1: Comments to Taxonomy."""
        
        print(Formatter.format_step_progress(1, "Creating taxonomy", self.provider.config.name))
        
        # Create taxonomy using weave decorator
        with weave.attributes({
            "model": self.provider.config.model,
            "provider": self.provider.config.name,
            "stage": "1_comments_to_tree"
        }):
            response = self.create_taxonomy(comments)
        
        # Calculate cost
        cost = self.provider.calculate_cost(response.usage)
        
        # Extract metrics
        taxonomy_dict = response.taxonomy.to_dict()
        num_themes = response.taxonomy.get_num_themes()
        num_topics = response.taxonomy.get_num_topics()
        subtopics_counts = response.taxonomy.get_subtopics_counts()
        
        # Print results
        print("✅ Taxonomy created successfully!")
        print(f"📊 Themes: {num_themes}, Topics: {num_topics}")
        print(f"🔢 Token usage: {response.usage.total_tokens} total ({response.usage.prompt_tokens} in, {response.usage.completion_tokens} out)")
        print(Formatter.format_taxonomy_tree(taxonomy_dict))
        
        # Log to W&B
        usage_stats = {
            "total_tokens": response.usage.total_tokens,
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens
        }
        self.logger.log_taxonomy_step(taxonomy_dict, usage_stats, comments, cost)
        
        # Print cost
        print(f"💰 Step 1 cost: ${cost:.4f}")
        
        return {
            "taxonomy": response.taxonomy,
            "taxonomy_dict": taxonomy_dict,
            "usage": response.usage,
            "cost": cost,
            "num_themes": num_themes,
            "num_topics": num_topics,
            "subtopics_counts": subtopics_counts
        } 