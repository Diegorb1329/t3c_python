"""
Step 2: Comments to Claims
For each comment, extract all claims and assign them to a specific topic node in the taxonomy tree.
"""

import weave
from typing import List, Dict, Any

from providers.base_provider import BaseLLMProvider
from prompts.prompts import SystemPrompts
from models.taxonomy import Taxonomy
from models.claims import ClaimsResponse, ClaimsExtraction
from utils.formatting import Formatter
from utils.logging_utils import Logger


class ClaimsExtractor:
    """Step 2: Extract claims from comments."""
    
    def __init__(self, provider: BaseLLMProvider, logger: Logger):
        """Initialize claims extractor."""
        self.provider = provider
        self.logger = logger
    
    @weave.op()
    def extract_claims(self, taxonomy_dict: Dict[str, Any], comment: str) -> ClaimsResponse:
        """Extract claims from a comment using the LLM provider."""
        
        # Create prompts
        system_prompt = SystemPrompts.SYSTEM_PROMPT
        user_prompt = SystemPrompts.get_claims_prompt(taxonomy_dict, comment)
        
        # Call LLM provider
        response = self.provider.extract_claims(system_prompt, user_prompt)
        
        return response
    
    def execute(self, taxonomy: Taxonomy, comments: List[str]) -> Dict[str, Any]:
        """Execute Step 2: Comments to Claims."""
        
        print(Formatter.format_step_progress(2, "Extracting claims", self.provider.config.name))
        
        taxonomy_dict = taxonomy.to_dict()
        
        # Track totals
        total_usage = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        total_cost = 0.0
        all_claims = []
        claims_data_for_logging = []
        
        # Process each comment
        with weave.attributes({
            "model": self.provider.config.model,
            "provider": self.provider.config.name,
            "stage": "2_comment_to_claims"
        }):
            for i, comment in enumerate(comments):
                print(f"   Processing comment {i+1}/{len(comments)}...")
                
                # Extract claims
                response = self.extract_claims(taxonomy_dict, comment)
                
                # Calculate cost
                cost = self.provider.calculate_cost(response.usage)
                total_cost += cost
                
                # Update totals
                total_usage["total_tokens"] += response.usage.total_tokens
                total_usage["input_tokens"] += response.usage.prompt_tokens
                total_usage["output_tokens"] += response.usage.completion_tokens
                
                # Store claims
                all_claims.append(response.claims_extraction)
                
                # Prepare logging data
                claims_dict = response.claims_extraction.to_dict()
                claims_html = Formatter.cute_print(claims_dict)
                claims_data_for_logging.append([
                    comment,
                    claims_html,
                    Formatter.format_json_pretty(claims_dict)
                ])
                
                # Print progress
                num_claims = response.claims_extraction.get_num_claims()
                print(Formatter.format_claims_summary(comment, num_claims))
                
                # Log individual step
                usage_stats = {
                    "total_tokens": response.usage.total_tokens,
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
                self.logger.log_claims_step(comment, claims_dict, usage_stats, total_usage)
        
        # Log summary
        self.logger.log_claims_summary(claims_data_for_logging, total_cost)
        
        # Print completion
        print(f"✅ Step 2 completed!")
        print(f"💰 Step 2 cost: ${total_cost:.4f}")
        
        return {
            "all_claims": all_claims,
            "claims_data_for_logging": claims_data_for_logging,
            "total_usage": total_usage,
            "total_cost": total_cost
        } 