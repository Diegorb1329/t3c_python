"""
Data models for the final T3C report.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from datetime import datetime
from openai.types import CompletionUsage


@dataclass
class TokenUsage:
    """Represents token usage across all pipeline steps."""
    total_tokens: int
    input_tokens: int
    output_tokens: int
    
    def __init__(self):
        self.total_tokens = 0
        self.input_tokens = 0
        self.output_tokens = 0
    
    def add_usage(self, usage: CompletionUsage):
        """Add usage from a single LLM call."""
        self.total_tokens += usage.total_tokens
        self.input_tokens += usage.prompt_tokens
        self.output_tokens += usage.completion_tokens


@dataclass
class StepCost:
    """Represents cost for a single pipeline step."""
    step_name: str
    cost: float
    token_usage: TokenUsage
    
    def __init__(self, step_name: str, cost: float, usage: CompletionUsage):
        self.step_name = step_name
        self.cost = cost
        self.token_usage = TokenUsage()
        self.token_usage.add_usage(usage)


@dataclass
class CostSummary:
    """Represents cost summary for the entire pipeline."""
    estimated_cost: float
    actual_cost: float
    token_based_cost: float
    step_costs: List[StepCost]
    provider_name: str
    model_name: str
    
    def __init__(self, provider_name: str, model_name: str, estimated_cost: float):
        self.provider_name = provider_name
        self.model_name = model_name
        self.estimated_cost = estimated_cost
        self.actual_cost = 0.0
        self.token_based_cost = 0.0
        self.step_costs = []
    
    def add_step_cost(self, step_cost: StepCost):
        """Add cost for a pipeline step."""
        self.step_costs.append(step_cost)
        self.actual_cost += step_cost.cost
    
    def get_accuracy_percentage(self) -> float:
        """Get accuracy of cost estimation."""
        if self.estimated_cost == 0:
            return 0.0
        return (self.actual_cost / self.estimated_cost) * 100
    
    def get_openai_equivalent_cost(self) -> float:
        """Estimate OpenAI equivalent cost (rough approximation)."""
        return self.actual_cost * 13.33  # Rough 13x cost difference
    
    def get_savings_vs_openai(self) -> Tuple[float, float]:
        """Get savings amount and percentage vs OpenAI."""
        openai_cost = self.get_openai_equivalent_cost()
        savings = openai_cost - self.actual_cost
        percentage = (savings / openai_cost) * 100 if openai_cost > 0 else 0
        return savings, percentage


@dataclass
class PipelineStats:
    """Represents pipeline execution statistics."""
    comments_processed: int
    themes_identified: int
    topics_identified: int
    claims_extracted: int
    duplicate_groups: int
    total_tokens_used: int
    processing_time: float
    
    def __init__(self):
        self.comments_processed = 0
        self.themes_identified = 0
        self.topics_identified = 0
        self.claims_extracted = 0
        self.duplicate_groups = 0
        self.total_tokens_used = 0
        self.processing_time = 0.0


@dataclass
class ReportTopic:
    """Represents a topic in the final report."""
    topic_name: str
    total_claims: int
    claims: List[str]
    
    def __init__(self, topic_name: str, claims: List[str]):
        self.topic_name = topic_name
        self.claims = claims
        self.total_claims = len(claims)


@dataclass
class ReportTheme:
    """Represents a theme in the final report."""
    theme_name: str
    total_claims: int
    topics: List[ReportTopic]
    
    def __init__(self, theme_name: str, topics: List[ReportTopic]):
        self.theme_name = theme_name
        self.topics = topics
        self.total_claims = sum(topic.total_claims for topic in topics)


@dataclass
class T3CReport:
    """Represents the final T3C report."""
    themes: List[ReportTheme]
    pipeline_stats: PipelineStats
    cost_summary: CostSummary
    run_name: str
    timestamp: datetime
    structured_json: Dict[str, Any] = None  # New field for structured JSON output
    
    def __init__(self, run_name: str, cost_summary: CostSummary):
        self.run_name = run_name
        self.timestamp = datetime.now()
        self.themes = []
        self.pipeline_stats = PipelineStats()
        self.cost_summary = cost_summary
    
    def add_theme(self, theme: ReportTheme):
        """Add a theme to the report."""
        self.themes.append(theme)
    
    def get_total_themes(self) -> int:
        """Get total number of themes."""
        return len(self.themes)
    
    def get_total_topics(self) -> int:
        """Get total number of topics."""
        return sum(len(theme.topics) for theme in self.themes)
    
    def get_total_claims(self) -> int:
        """Get total number of claims."""
        return sum(theme.total_claims for theme in self.themes)
    
    def to_csv_log(self, exp_group: str) -> str:
        """Generate CSV log entry."""
        from pytz import timezone
        import pytz
        
        date_format = '%m/%d/%Y %H:%M:%S'
        date = datetime.now()
        date = date.astimezone(timezone('US/Pacific'))
        time_str = date.strftime(date_format)
        
        # Get step costs
        step_costs = {step.step_name: step.cost for step in self.cost_summary.step_costs}
        
        log_row = [
            self.run_name,
            exp_group,
            time_str,
            self.pipeline_stats.comments_processed,
            "N/A",  # character count placeholder
            round(self.cost_summary.estimated_cost, 4),
            round(self.cost_summary.token_based_cost, 4),
            round(self.cost_summary.actual_cost, 4),
            round(step_costs.get("taxonomy", 0), 4),
            round(step_costs.get("claims", 0), 4),
            round(step_costs.get("deduplication", 0), 4),
            self.pipeline_stats.themes_identified,
            self.pipeline_stats.topics_identified,
            self.pipeline_stats.claims_extracted
        ]
        
        return ",".join([str(x) for x in log_row])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "run_name": self.run_name,
            "timestamp": self.timestamp.isoformat(),
            "themes": [
                {
                    "theme_name": theme.theme_name,
                    "total_claims": theme.total_claims,
                    "topics": [
                        {
                            "topic_name": topic.topic_name,
                            "total_claims": topic.total_claims,
                            "claims": topic.claims
                        }
                        for topic in theme.topics
                    ]
                }
                for theme in self.themes
            ],
            "pipeline_stats": {
                "comments_processed": self.pipeline_stats.comments_processed,
                "themes_identified": self.pipeline_stats.themes_identified,
                "topics_identified": self.pipeline_stats.topics_identified,
                "claims_extracted": self.pipeline_stats.claims_extracted,
                "duplicate_groups": self.pipeline_stats.duplicate_groups,
                "total_tokens_used": self.pipeline_stats.total_tokens_used,
                "processing_time": self.pipeline_stats.processing_time
            },
            "cost_summary": {
                "provider_name": self.cost_summary.provider_name,
                "model_name": self.cost_summary.model_name,
                "estimated_cost": self.cost_summary.estimated_cost,
                "actual_cost": self.cost_summary.actual_cost,
                "token_based_cost": self.cost_summary.token_based_cost,
                "accuracy_percentage": self.cost_summary.get_accuracy_percentage(),
                "step_costs": [
                    {
                        "step_name": step.step_name,
                        "cost": step.cost,
                        "tokens": step.token_usage.total_tokens
                    }
                    for step in self.cost_summary.step_costs
                ]
            }
        } 