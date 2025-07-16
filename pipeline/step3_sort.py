"""
Step 3: Sort by Claims Frequency
Sort the themes and topics by claim frequency so that the most discussed topics appear first.
This step does not require LLM calls.
"""

from typing import List, Dict, Any

from models.claims import ClaimsExtraction, SortedTaxonomy, TopicClaims, SubtopicClaims
from utils.formatting import Formatter
from utils.logging_utils import Logger


class TaxonomySorter:
    """Step 3: Sort taxonomy by claim frequency."""
    
    def __init__(self, logger: Logger):
        """Initialize taxonomy sorter."""
        self.logger = logger
    
    def sort_taxonomy(self, taxonomy_dict: Dict[str, Any], all_claims: List[ClaimsExtraction], 
                     comments: List[str]) -> SortedTaxonomy:
        """Sort taxonomy by claim frequency."""
        
        # Build claim counts by topic/subtopic
        topic_claims = {}
        
        # Process each comment's claims
        for comment, claims_extraction in zip(comments, all_claims):
            for claim in claims_extraction.claims:
                topic_name = claim.topic_name
                subtopic_name = claim.subtopic_name
                
                # Initialize topic if not exists
                if topic_name not in topic_claims:
                    topic_claims[topic_name] = {}
                
                # Initialize subtopic if not exists
                if subtopic_name not in topic_claims[topic_name]:
                    topic_claims[topic_name][subtopic_name] = []
                
                # Add claim text
                topic_claims[topic_name][subtopic_name].append(claim.claim)
        
        # Convert to structured format
        structured_topics = {}
        for topic_name, subtopics in topic_claims.items():
            subtopic_claims = {}
            for subtopic_name, claims in subtopics.items():
                subtopic_claims[subtopic_name] = SubtopicClaims(subtopic_name, claims)
            
            structured_topics[topic_name] = TopicClaims(topic_name, subtopic_claims)
        
        return SortedTaxonomy(structured_topics)
    
    def execute(self, taxonomy_dict: Dict[str, Any], all_claims: List[ClaimsExtraction], 
                comments: List[str]) -> Dict[str, Any]:
        """Execute Step 3: Sort by Claims Frequency."""
        
        print(Formatter.format_step_progress(3, "Sorting taxonomy (no LLM calls)", "N/A"))
        
        # Sort the taxonomy
        sorted_taxonomy = self.sort_taxonomy(taxonomy_dict, all_claims, comments)
        
        # Calculate metrics
        total_topics = sorted_taxonomy.get_total_topics()
        total_claims = sorted_taxonomy.get_total_claims()
        
        print("✅ Taxonomy sorted successfully!")
        print(f"📊 Total topics: {total_topics}, Total claims: {total_claims}")
        
        # Convert to legacy format for compatibility
        legacy_format = {}
        for topic_name, topic_claims in sorted_taxonomy.topics.items():
            legacy_format[topic_name] = {
                "total": topic_claims.total_count,
                "subtopics": {}
            }
            for subtopic_name, subtopic_claims in topic_claims.subtopics.items():
                legacy_format[topic_name]["subtopics"][subtopic_name] = {
                    "total": subtopic_claims.total_count,
                    "claims": subtopic_claims.claims
                }
        
        # Log to W&B
        self.logger.log_sorting_step(legacy_format)
        
        return {
            "sorted_taxonomy": sorted_taxonomy,
            "legacy_format": legacy_format,
            "total_topics": total_topics,
            "total_claims": total_claims
        } 