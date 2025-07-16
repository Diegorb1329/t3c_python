"""
Logging utilities for W&B and Weave integration.
"""

import wandb
import weave
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
from pytz import timezone

from config import Config, RuntimeConfig
from models.report import T3CReport
from utils.formatting import Formatter


class Logger:
    """Utility for logging to W&B and Weave."""
    
    def __init__(self, runtime_config: RuntimeConfig):
        """Initialize logger with runtime configuration."""
        self.runtime_config = runtime_config
        self.initialized = False
        self.wandb_run = None
    
    def initialize(self, run_name: str, cost_estimate: float):
        """Initialize W&B and Weave logging."""
        if self.initialized:
            return
        
        if self.runtime_config.enable_weave:
            try:
                weave.init(Config.WB_PROJECT_NAME)
                print("✅ Weave initialized")
            except Exception as e:
                print(f"⚠️ Weave initialization failed: {e}")
        
        if self.runtime_config.enable_wandb:
            try:
                run_config = self.runtime_config.get_run_config()
                run_config["cost_guess"] = cost_estimate
                
                self.wandb_run = wandb.init(
                    project=Config.WB_PROJECT_NAME,
                    name=run_name,
                    group=self.runtime_config.exp_group,
                    config=run_config
                )
                print("✅ W&B initialized")
            except Exception as e:
                print(f"⚠️ W&B initialization failed: {e}")
        
        self.initialized = True
    
    def log_comment_stats(self, comments: List[str]):
        """Log comment statistics."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        comment_lengths = [len(c) for c in comments]
        
        try:
            wandb.log({
                "comm_N": len(comments),
                "comm_text_len": sum(comment_lengths),
                "comm_bins": comment_lengths
            })
        except Exception as e:
            print(f"⚠️ Failed to log comment stats: {e}")
    
    def log_taxonomy_step(self, taxonomy_dict: Dict[str, Any], usage_stats: Dict[str, Any], 
                         comments: List[str], cost: float):
        """Log taxonomy creation step."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            # Create formatted taxonomy for display
            comment_list = "\n".join(comments) if comments else "none"
            taxonomy_html = Formatter.cute_print(taxonomy_dict)
            
            table_data = [[
                comment_list,
                taxonomy_html,
                Formatter.format_json_pretty(taxonomy_dict)
            ]]
            
            # Calculate metrics
            num_themes = len(taxonomy_dict.get("taxonomy", []))
            subtopics = [len(t.get("subtopics", [])) for t in taxonomy_dict.get("taxonomy", [])]
            num_topics = sum(subtopics)
            
            wandb.log({
                "u/1/N_tok": usage_stats.get("total_tokens", 0),
                "u/1/in_tok": usage_stats.get("input_tokens", 0),
                "u/1/out_tok": usage_stats.get("output_tokens", 0),
                "u/1/cost": cost,
                "num_themes": num_themes,
                "num_topics": num_topics,
                "topic_tree": subtopics,
                "rows_to_tree": wandb.Table(
                    data=table_data,
                    columns=["comments", "taxonomy", "raw_llm_out"]
                )
            })
        except Exception as e:
            print(f"⚠️ Failed to log taxonomy step: {e}")
    
    def log_claims_step(self, comment: str, claims_dict: Dict[str, Any], 
                       usage_stats: Dict[str, Any], step_totals: Dict[str, Any]):
        """Log claims extraction step."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            wandb.log({
                "u/2/s_N_tok": usage_stats.get("total_tokens", 0),
                "u/2/s_in_tok": usage_stats.get("input_tokens", 0),
                "u/2/s_out_tok": usage_stats.get("output_tokens", 0),
                "u/2/t_N_tok": step_totals.get("total_tokens", 0),
                "u/2/t_in_tok": step_totals.get("input_tokens", 0),
                "u/2/t_out_tok": step_totals.get("output_tokens", 0)
            })
        except Exception as e:
            print(f"⚠️ Failed to log claims step: {e}")
    
    def log_claims_summary(self, all_claims_data: List[List[Any]], cost: float):
        """Log claims extraction summary."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            wandb.log({
                "u/2/cost": cost,
                "row_to_claims": wandb.Table(
                    data=all_claims_data,
                    columns=["comments", "claims", "raw_llm_out"]
                )
            })
        except Exception as e:
            print(f"⚠️ Failed to log claims summary: {e}")
    
    def log_sorting_step(self, sorted_taxonomy: Dict[str, Any]):
        """Log sorting step."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            html_data = [[
                Formatter.cute_print(sorted_taxonomy),
                Formatter.format_json_pretty(sorted_taxonomy)
            ]]
            
            wandb.log({
                "sort_tree": wandb.Table(
                    data=html_data,
                    columns=["sorted_taxonomy", "raw_llm_output"]
                )
            })
        except Exception as e:
            print(f"⚠️ Failed to log sorting step: {e}")
    
    def log_deduplication_step(self, usage_stats: Dict[str, Any], step_totals: Dict[str, Any]):
        """Log deduplication step."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            wandb.log({
                "u/4/s_N_tok": usage_stats.get("total_tokens", 0),
                "u/4/s_in_tok": usage_stats.get("input_tokens", 0),
                "u/4/s_out_tok": usage_stats.get("output_tokens", 0),
                "u/4/t_N_tok": step_totals.get("total_tokens", 0),
                "u/4/t_in_tok": step_totals.get("input_tokens", 0),
                "u/4/t_out_tok": step_totals.get("output_tokens", 0)
            })
        except Exception as e:
            print(f"⚠️ Failed to log deduplication step: {e}")
    
    def log_deduplication_summary(self, dedup_data: List[List[Any]], cost: float, 
                                 num_claims: int, num_topics: int):
        """Log deduplication summary."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            wandb.log({
                "u/4/cost": cost,
                "dedup_subclaims": wandb.Table(
                    data=dedup_data,
                    columns=["sub_claim_list", "deduped_claims", "raw_llm_output"]
                ),
                "num_claims": num_claims,
                "num_topics_post_sort": num_topics
            })
        except Exception as e:
            print(f"⚠️ Failed to log deduplication summary: {e}")
    
    def log_final_report(self, report: T3CReport):
        """Log final T3C report."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            # Create formatted report for display
            html_data = [[
                Formatter.cute_print(report.to_dict()),
                Formatter.format_json_pretty(report.to_dict())
            ]]
            
            # Log comprehensive metrics
            wandb.log({
                "cost/tok_total": report.cost_summary.token_based_cost,
                "cost/actual": report.cost_summary.actual_cost,
                "cost/1": next((step.cost for step in report.cost_summary.step_costs if step.step_name == "taxonomy"), 0),
                "cost/2": next((step.cost for step in report.cost_summary.step_costs if step.step_name == "claims"), 0),
                "cost/4": next((step.cost for step in report.cost_summary.step_costs if step.step_name == "deduplication"), 0),
                "csv_log": report.to_csv_log(self.runtime_config.exp_group),
                "provider_used": report.cost_summary.provider_name,
                "model_used": report.cost_summary.model_name,
                "t3c_report": wandb.Table(
                    data=html_data,
                    columns=["t3c_report", "raw_llm_output"]
                )
            })
        except Exception as e:
            print(f"⚠️ Failed to log final report: {e}")
    
    def log_cumulative_stats(self, total_stats: Dict[str, Any]):
        """Log cumulative statistics."""
        if not self.runtime_config.enable_wandb or not self.wandb_run:
            return
        
        try:
            wandb.log({
                "u/N/N_tok": total_stats.get("total_tokens", 0),
                "u/N/in_tok": total_stats.get("input_tokens", 0),
                "u/N/out_tok": total_stats.get("output_tokens", 0),
                "u/N/cost": total_stats.get("cost", 0)
            })
        except Exception as e:
            print(f"⚠️ Failed to log cumulative stats: {e}")
    
    def finish(self):
        """Finish logging session."""
        if self.wandb_run:
            try:
                self.wandb_run.finish()
                print("✅ W&B session finished")
            except Exception as e:
                print(f"⚠️ Failed to finish W&B session: {e}")
    
    @staticmethod
    def time_here() -> str:
        """Get current time in Pacific timezone."""
        date_format = '%m/%d/%Y %H:%M:%S'
        date = datetime.now()
        date = date.astimezone(timezone('US/Pacific'))
        return date.strftime(date_format) 