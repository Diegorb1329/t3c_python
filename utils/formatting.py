"""
Formatting utilities for the T3C pipeline.
"""

import json
from typing import Any, Dict, List
import wandb


class Formatter:
    """Utility for formatting output and reports."""
    
    @staticmethod
    def cute_print(json_obj: Any) -> wandb.Html:
        """Return a pretty version of a dictionary as properly-indented JSON in HTML for W&B."""
        if not isinstance(json_obj, (dict, list)):
            json_obj = str(json_obj)
        
        try:
            str_json = json.dumps(json_obj, indent=2)
        except (TypeError, ValueError):
            str_json = str(json_obj)
        
        cute_html = f'<pre id="json"><font size=2>{str_json}</font></pre>'
        return wandb.Html(cute_html)
    
    @staticmethod
    def format_cost_summary(cost_summary: Dict[str, Any]) -> str:
        """Format cost summary for console output."""
        output = []
        output.append(f"💰 COST SUMMARY for {cost_summary.get('provider_name', 'Unknown')}:")
        output.append(f"   Estimated: ${cost_summary.get('estimated_cost', 0):.4f}")
        output.append(f"   Actual: ${cost_summary.get('actual_cost', 0):.4f}")
        output.append(f"   Token-based: ${cost_summary.get('token_based_cost', 0):.4f}")
        output.append(f"   Accuracy: {cost_summary.get('accuracy_percentage', 0):.1f}% of estimate")
        
        return "\n".join(output)
    
    @staticmethod
    def format_pipeline_summary(stats: Dict[str, Any]) -> str:
        """Format pipeline statistics for console output."""
        output = []
        output.append("📊 PIPELINE SUMMARY:")
        output.append(f"   Provider: {stats.get('provider', 'Unknown')}")
        output.append(f"   Model: {stats.get('model', 'Unknown')}")
        output.append(f"   Comments processed: {stats.get('comments_processed', 0)}")
        output.append(f"   Themes identified: {stats.get('themes_identified', 0)}")
        output.append(f"   Topics identified: {stats.get('topics_identified', 0)}")
        output.append(f"   Claims extracted: {stats.get('claims_extracted', 0)}")
        output.append(f"   Duplicate groups: {stats.get('duplicate_groups', 0)}")
        output.append(f"   Total tokens used: {stats.get('total_tokens_used', 0):,}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_provider_comparison(comparison: Dict[str, Any]) -> str:
        """Format provider cost comparison for console output."""
        output = []
        output.append("💰 PROVIDER COST COMPARISON:")
        
        # Sort by cost
        sorted_providers = sorted(comparison.items(), key=lambda x: x[1]['cost'])
        
        for provider_key, info in sorted_providers:
            output.append(f"   {info['name']}: ${info['cost']:.4f} ({info['model']})")
        
        if len(sorted_providers) > 1:
            cheapest = sorted_providers[0][1]
            most_expensive = sorted_providers[-1][1]
            savings = most_expensive['cost'] - cheapest['cost']
            percentage = (savings / most_expensive['cost']) * 100
            
            output.append("")
            output.append(f"   💡 Cheapest: {cheapest['name']} - ${cheapest['cost']:.4f}")
            output.append(f"   💰 Savings vs most expensive: ${savings:.4f} ({percentage:.1f}%)")
        
        return "\n".join(output)
    
    @staticmethod
    def format_step_progress(step_num: int, step_name: str, provider_name: str) -> str:
        """Format step progress message."""
        return f"🚀 Step {step_num}: {step_name} using {provider_name}..."
    
    @staticmethod
    def format_step_completion(step_num: int, stats: Dict[str, Any]) -> str:
        """Format step completion message."""
        output = [f"✅ Step {step_num} completed!"]
        
        if 'cost' in stats:
            output.append(f"💰 Step {step_num} cost: ${stats['cost']:.4f}")
        
        if 'tokens' in stats:
            output.append(f"🔢 Token usage: {stats['tokens']} total")
        
        if 'items_processed' in stats:
            output.append(f"📊 Items processed: {stats['items_processed']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_taxonomy_tree(taxonomy_dict: Dict[str, Any]) -> str:
        """Format taxonomy tree for console display."""
        output = []
        output.append("📋 Topics found:")
        
        if 'taxonomy' in taxonomy_dict:
            for topic in taxonomy_dict['taxonomy']:
                output.append(f"  🎯 {topic['topicName']}:")
                for subtopic in topic.get('subtopics', []):
                    output.append(f"    - {subtopic['subtopicName']}")
        
        return "\n".join(output)
    
    @staticmethod
    def format_claims_summary(comment: str, num_claims: int, max_length: int = 50) -> str:
        """Format claims extraction summary."""
        truncated_comment = comment[:max_length] + "..." if len(comment) > max_length else comment
        return f"   📝 Comment: {truncated_comment}\n   🎯 Claims extracted: {num_claims}"
    
    @staticmethod
    def format_duplicate_summary(duplicate_groups: Dict[str, List[str]]) -> str:
        """Format duplicate groups summary."""
        if not duplicate_groups:
            return "🔍 No duplicates found"
        
        output = [f"🔍 Duplicate groups found: {len(duplicate_groups)}"]
        for main_claim, duplicates in duplicate_groups.items():
            if duplicates:  # Only show groups with actual duplicates
                output.append(f"  📝 {main_claim}")
                output.append(f"    📋 Duplicates: {len(duplicates)}")
        
        return "\n".join(output)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to specified length."""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    @staticmethod
    def format_json_pretty(data: Any, indent: int = 2) -> str:
        """Format JSON data with pretty printing."""
        try:
            return json.dumps(data, indent=indent, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(data) 