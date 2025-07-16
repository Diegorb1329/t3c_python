"""
Step 4: Deduplicate Claims
Find similar claims in each subtopic and group them together.
"""

import weave
from typing import List, Dict, Any

from providers.base_provider import BaseLLMProvider
from prompts.prompts import SystemPrompts
from models.claims import DeduplicationResponse, SortedTaxonomy
from utils.formatting import Formatter
from utils.logging_utils import Logger


class ClaimsDeduplicator:
    """Step 4: Deduplicate claims in each subtopic."""
    
    def __init__(self, provider: BaseLLMProvider, logger: Logger):
        """Initialize claims deduplicator."""
        self.provider = provider
        self.logger = logger
    
    @weave.op()
    def deduplicate_claims(self, claims: List[str]) -> DeduplicationResponse:
        """Deduplicate claims using the LLM provider."""
        
        # Create prompts
        system_prompt = SystemPrompts.SYSTEM_PROMPT
        user_prompt = SystemPrompts.get_dedup_prompt(claims)
        
        # Call LLM provider
        response = self.provider.deduplicate_claims(system_prompt, user_prompt)
        
        return response
    
    def execute(self, sorted_taxonomy: SortedTaxonomy) -> Dict[str, Any]:
        """Execute Step 4: Deduplicate Claims."""
        
        print(Formatter.format_step_progress(4, "Deduplicating claims", self.provider.config.name))
        
        # Track totals
        total_usage = {
            "total_tokens": 0,
            "input_tokens": 0,
            "output_tokens": 0
        }
        total_cost = 0.0
        
        nested_claims = {}
        duplicate_groups = {}
        dedup_data_for_logging = []
        topics_processed = 0
        
        # Process each topic and subtopic
        with weave.attributes({
            "model": self.provider.config.model,
            "provider": self.provider.config.name,
            "stage": "4_dedup_claims"
        }):
            for topic_name, topic_claims in sorted_taxonomy.topics.items():
                for subtopic_name, subtopic_claims in topic_claims.subtopics.items():
                    topics_processed += 1
                    claims_list = subtopic_claims.claims
                    
                    print(f"   Processing topic {topics_processed}: {subtopic_name} ({len(claims_list)} claims)")
                    
                    # Skip topics with only one claim
                    if len(claims_list) <= 1:
                        print(f"     ⏭️  Skipping {subtopic_name} (only {len(claims_list)} claim)")
                        continue
                    
                    # Deduplicate claims
                    response = self.deduplicate_claims(claims_list)
                    
                    # Calculate cost
                    cost = self.provider.calculate_cost(response.usage)
                    total_cost += cost
                    
                    # Update totals
                    total_usage["total_tokens"] += response.usage.total_tokens
                    total_usage["input_tokens"] += response.usage.prompt_tokens
                    total_usage["output_tokens"] += response.usage.completion_tokens
                    
                    # Check for duplicates
                    has_duplicates = response.deduplication_result.has_duplicates()
                    
                    if has_duplicates:
                        # Store duplicate information
                        nested_claims[subtopic_name] = {
                            "dupes": response.deduplication_result.to_dict(),
                            "og": claims_list
                        }
                        
                        # Extract duplicate groups
                        for claim_key, claim_vals in response.deduplication_result.nesting.items():
                            if len(claim_vals) > 0:
                                # Extract index from claim key (e.g., "claimId2" -> 2)
                                try:
                                    main_claim_idx = int(claim_key.replace("claimId", ""))
                                    duplicate_indices = [int(c_key.replace("claimId", "")) for c_key in claim_vals]
                                    
                                    main_claim = claims_list[main_claim_idx]
                                    duplicate_groups[main_claim] = duplicate_indices
                                except (ValueError, IndexError):
                                    print(f"     ⚠️  Error processing claim indices for {subtopic_name}")
                        
                        print(f"     🔍 Found duplicates in {subtopic_name}")
                    
                    # Prepare logging data
                    dedup_dict = response.deduplication_result.to_dict()
                    dedup_data_for_logging.append([
                        "\n".join(claims_list),
                        Formatter.cute_print(dedup_dict),
                        Formatter.format_json_pretty(dedup_dict)
                    ])
                    
                    # Log individual step
                    usage_stats = {
                        "total_tokens": response.usage.total_tokens,
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens
                    }
                    self.logger.log_deduplication_step(usage_stats, total_usage)
        
        # Log summary
        total_topics = sorted_taxonomy.get_total_topics()
        total_claims = sorted_taxonomy.get_total_claims()
        self.logger.log_deduplication_summary(dedup_data_for_logging, total_cost, total_claims, total_topics)
        
        # Print completion
        print(f"✅ Step 4 completed!")
        print(f"💰 Step 4 cost: ${total_cost:.4f}")
        print(Formatter.format_duplicate_summary(duplicate_groups))
        
        return {
            "nested_claims": nested_claims,
            "duplicate_groups": duplicate_groups,
            "dedup_data_for_logging": dedup_data_for_logging,
            "total_usage": total_usage,
            "total_cost": total_cost,
            "topics_processed": topics_processed
        } 