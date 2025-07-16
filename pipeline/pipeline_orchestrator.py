"""
Pipeline Orchestrator
Coordinates all pipeline steps and generates the final T3C report.
"""

import time
from typing import List, Dict, Any

from providers.base_provider import BaseLLMProvider
from models.report import T3CReport, CostSummary, StepCost, ReportTheme, ReportTopic
from utils.cost_estimator import CostEstimator
from utils.data_loader import DataLoader
from utils.formatting import Formatter
from utils.logging_utils import Logger
from pipeline.step1_taxonomy import TaxonomyCreator
from pipeline.step2_claims import ClaimsExtractor
from pipeline.step3_sort import TaxonomySorter
from pipeline.step4_dedup import ClaimsDeduplicator
from pipeline.step5_json_output import StructuredJSONGenerator


class PipelineOrchestrator:
    """Orchestrates the complete T3C pipeline."""
    
    def __init__(self, provider: BaseLLMProvider, logger: Logger):
        """Initialize pipeline orchestrator."""
        self.provider = provider
        self.logger = logger
        
        # Initialize pipeline steps
        self.taxonomy_creator = TaxonomyCreator(provider, logger)
        self.claims_extractor = ClaimsExtractor(provider, logger)
        self.taxonomy_sorter = TaxonomySorter(logger)
        self.claims_deduplicator = ClaimsDeduplicator(provider, logger)
        self.json_generator = StructuredJSONGenerator(provider, logger)
    
    def execute_pipeline(self, comments: List[str], run_name: str) -> T3CReport:
        """Execute the complete T3C pipeline."""
        
        start_time = time.time()
        
        # Validate and prepare comments
        comments, original_count, final_count = DataLoader.validate_comments(comments)
        comment_stats = DataLoader.get_comment_stats(comments)
        
        print(f"📊 Processing {final_count} comments ({original_count} original)")
        print(f"📊 Total characters: {comment_stats['total_chars']}, Average length: {comment_stats['avg_length']:.1f}")
        
        # Estimate costs
        cost_estimator = CostEstimator(self.provider.config)
        estimated_cost = cost_estimator.estimate_total_cost(comments)
        cost_breakdown = cost_estimator.get_cost_breakdown(comments)
        
        print(f"💰 Estimated cost: ${estimated_cost:.4f}")
        print(f"💰 Cost breakdown: {cost_breakdown}")
        
        # Initialize logging
        self.logger.initialize(run_name, estimated_cost)
        self.logger.log_comment_stats(comments)
        
        # Create cost summary
        cost_summary = CostSummary(
            provider_name=self.provider.config.name,
            model_name=self.provider.config.model,
            estimated_cost=estimated_cost
        )
        
        # Initialize report
        report = T3CReport(run_name, cost_summary)
        report.pipeline_stats.comments_processed = final_count
        
        # Step 1: Create taxonomy
        print(f"\n{Formatter.format_step_progress(1, 'Creating taxonomy', self.provider.config.name)}")
        step1_result = self.taxonomy_creator.execute(comments)
        
        step1_cost = StepCost("taxonomy", step1_result["cost"], step1_result["usage"])
        cost_summary.add_step_cost(step1_cost)
        
        report.pipeline_stats.themes_identified = step1_result["num_themes"]
        report.pipeline_stats.topics_identified = step1_result["num_topics"]
        
        # Step 2: Extract claims
        print(f"\n{Formatter.format_step_progress(2, 'Extracting claims', self.provider.config.name)}")
        step2_result = self.claims_extractor.execute(step1_result["taxonomy"], comments)
        
        # Create a proper CompletionUsage object from the dictionary
        from openai.types import CompletionUsage
        step2_usage = CompletionUsage(
            prompt_tokens=step2_result["total_usage"]["input_tokens"],
            completion_tokens=step2_result["total_usage"]["output_tokens"],
            total_tokens=step2_result["total_usage"]["total_tokens"]
        )
        step2_cost = StepCost("claims", step2_result["total_cost"], step2_usage)
        cost_summary.add_step_cost(step2_cost)
        
        # Step 3: Sort taxonomy
        print(f"\n{Formatter.format_step_progress(3, 'Sorting taxonomy', 'N/A')}")
        step3_result = self.taxonomy_sorter.execute(
            step1_result["taxonomy_dict"], 
            step2_result["all_claims"], 
            comments
        )
        
        report.pipeline_stats.claims_extracted = step3_result["total_claims"]
        
        # Step 4: Deduplicate claims
        print(f"\n{Formatter.format_step_progress(4, 'Deduplicating claims', self.provider.config.name)}")
        step4_result = self.claims_deduplicator.execute(step3_result["sorted_taxonomy"])
        
        # Create a proper CompletionUsage object from the dictionary
        step4_usage = CompletionUsage(
            prompt_tokens=step4_result["total_usage"]["input_tokens"],
            completion_tokens=step4_result["total_usage"]["output_tokens"],
            total_tokens=step4_result["total_usage"]["total_tokens"]
        )
        step4_cost = StepCost("deduplication", step4_result["total_cost"], step4_usage)
        cost_summary.add_step_cost(step4_cost)
        
        report.pipeline_stats.duplicate_groups = len(step4_result["duplicate_groups"])
        
        # Calculate final statistics
        end_time = time.time()
        processing_time = end_time - start_time
        
        report.pipeline_stats.processing_time = processing_time
        report.pipeline_stats.total_tokens_used = (
            step1_result["usage"].total_tokens +
            step2_result["total_usage"]["total_tokens"] +
            step4_result["total_usage"]["total_tokens"]
        )
        
        # Generate final report themes
        report_themes = self._generate_report_themes(
            step3_result["sorted_taxonomy"], 
            step4_result["duplicate_groups"]
        )
        
        for theme in report_themes:
            report.add_theme(theme)
        
        # Step 5: Generate structured JSON output
        print(f"\n{Formatter.format_step_progress(5, 'Generating structured JSON', self.provider.config.name)}")
        step5_result = self.json_generator.execute(report, comments, run_name)
        
        if step5_result["success"]:
            report.structured_json = step5_result["structured_json"]
            
            # Add step 5 cost to summary
            from openai.types import CompletionUsage
            step5_usage = CompletionUsage(
                prompt_tokens=step5_result["usage"].prompt_tokens,
                completion_tokens=step5_result["usage"].completion_tokens,
                total_tokens=step5_result["usage"].total_tokens
            )
            step5_cost = StepCost("structured_json", step5_result["cost"], step5_usage)
            cost_summary.add_step_cost(step5_cost)
            
            # Update total tokens
            report.pipeline_stats.total_tokens_used += step5_result["usage"].total_tokens
        
        # Update cost summary with token-based calculation
        total_tokens = report.pipeline_stats.total_tokens_used
        cost_summary.token_based_cost = cost_summary.actual_cost
        
        # Log final report
        self.logger.log_final_report(report)
        
        # Print final summary
        self._print_final_summary(report, cost_breakdown, processing_time)
        
        return report
    
    def _generate_report_themes(self, sorted_taxonomy, duplicate_groups) -> List[ReportTheme]:
        """Generate report themes with deduplicated claims."""
        themes = []
        
        # Sort topics by claim count
        sorted_topics = sorted(
            sorted_taxonomy.topics.items(),
            key=lambda x: x[1].total_count,
            reverse=True
        )
        
        for topic_name, topic_claims in sorted_topics:
            # Create report topics
            report_topics = []
            
            # Sort subtopics by claim count
            sorted_subtopics = sorted(
                topic_claims.subtopics.items(),
                key=lambda x: x[1].total_count,
                reverse=True
            )
            
            for subtopic_name, subtopic_claims in sorted_subtopics:
                # Apply deduplication
                processed_claims = self._apply_deduplication(
                    subtopic_claims.claims, 
                    duplicate_groups
                )
                
                report_topic = ReportTopic(subtopic_name, processed_claims)
                report_topics.append(report_topic)
            
            theme = ReportTheme(topic_name, report_topics)
            themes.append(theme)
        
        return themes
    
    def _apply_deduplication(self, claims: List[str], duplicate_groups: Dict[str, List[int]]) -> List[str]:
        """Apply deduplication to claims list."""
        processed_claims = []
        
        for claim in claims:
            if claim in duplicate_groups:
                # This claim has duplicates
                duplicate_count = len(duplicate_groups[claim]) + 1
                processed_claim = f"{claim} ({duplicate_count}x)"
                processed_claims.append(processed_claim)
            else:
                processed_claims.append(claim)
        
        return processed_claims
    
    def _print_final_summary(self, report: T3CReport, cost_breakdown: Dict[str, Any], 
                           processing_time: float):
        """Print final pipeline summary."""
        print(f"\n🚀 Generating final T3C report...")
        
        # Cost summary
        cost_summary = report.cost_summary
        print(f"\n{Formatter.format_cost_summary(cost_summary.__dict__)}")
        
        if cost_summary.provider_name == "OpenRouter (Gemini 2.0 Flash)":
            openai_cost = cost_summary.get_openai_equivalent_cost()
            savings, percentage = cost_summary.get_savings_vs_openai()
            print(f"   💡 OpenAI equivalent cost: ~${openai_cost:.4f}")
            print(f"   💰 Savings vs OpenAI: ~${savings:.4f} ({percentage:.1f}%)")
        
        # Pipeline summary
        pipeline_stats = {
            "provider": cost_summary.provider_name,
            "model": cost_summary.model_name,
            "comments_processed": report.pipeline_stats.comments_processed,
            "themes_identified": report.pipeline_stats.themes_identified,
            "topics_identified": report.pipeline_stats.topics_identified,
            "claims_extracted": report.pipeline_stats.claims_extracted,
            "duplicate_groups": report.pipeline_stats.duplicate_groups,
            "total_tokens_used": report.pipeline_stats.total_tokens_used
        }
        
        print(f"\n{Formatter.format_pipeline_summary(pipeline_stats)}")
        print(f"   Processing time: {processing_time:.2f} seconds")
        
        # CSV log
        csv_log = report.to_csv_log(self.logger.runtime_config.exp_group)
        print(f"\n📋 CSV Log: {csv_log}")
        
        print(f"\n✅ Pipeline completed successfully with {cost_summary.provider_name}!")
        print(f"📊 Final report generated and logged to W&B") 