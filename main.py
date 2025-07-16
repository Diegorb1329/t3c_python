#!/usr/bin/env python3
"""
T3C Pipeline Main Entry Point

This script provides the main entry point for the T3C (Talk to the City) pipeline.
It can be run with different data sources and configuration options.
"""

import argparse
import sys
import os
from typing import List, Optional

# Add the current directory to Python path to allow relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, RuntimeConfig
from providers.provider_factory import ProviderFactory
from utils.data_loader import DataLoader
from utils.cost_estimator import CostEstimator
from utils.logging_utils import Logger
from utils.formatting import Formatter
from pipeline.pipeline_orchestrator import PipelineOrchestrator


def setup_argument_parser() -> argparse.ArgumentParser:
    """Set up command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="T3C Pipeline: Analyze and organize diverse human perspectives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with test data using OpenRouter
  python main.py --test-data scifi --provider openrouter --run-name "scifi_test"
  
  # Run with CSV file using OpenAI
  python main.py --csv-file data.csv --provider openai --run-name "csv_analysis"
  
  # Run with custom comments using OpenRouter
  python main.py --comments "I love AI" "AI is scary" --provider openrouter
  
  # Compare costs across providers
  python main.py --test-data pets --compare-costs
        """
    )
    
    # Data source options (mutually exclusive)
    data_group = parser.add_mutually_exclusive_group(required=True)
    data_group.add_argument(
        "--csv-file",
        type=str,
        help="Path to CSV file containing comments"
    )
    data_group.add_argument(
        "--test-data",
        choices=["scifi", "pets"],
        help="Use built-in test data"
    )
    data_group.add_argument(
        "--comments",
        nargs="+",
        help="List of comments to analyze"
    )
    
    # Provider configuration
    parser.add_argument(
        "--provider",
        choices=["openai", "openrouter"],
        default=Config.DEFAULT_PROVIDER,
        help=f"LLM provider to use (default: {Config.DEFAULT_PROVIDER})"
    )
    
    # Run configuration
    parser.add_argument(
        "--run-name",
        type=str,
        help="Name for the W&B run (auto-generated if not provided)"
    )
    parser.add_argument(
        "--exp-group",
        type=str,
        default=Config.DEFAULT_EXP_GROUP,
        help=f"Experiment group for W&B (default: {Config.DEFAULT_EXP_GROUP})"
    )
    
    # CSV specific options
    parser.add_argument(
        "--csv-column",
        type=str,
        default="comment",
        help="Column name containing comments in CSV file (default: comment)"
    )
    
    # Logging options
    parser.add_argument(
        "--no-wandb",
        action="store_true",
        help="Disable W&B logging"
    )
    parser.add_argument(
        "--no-weave",
        action="store_true",
        help="Disable Weave logging"
    )
    
    # Utility options
    parser.add_argument(
        "--compare-costs",
        action="store_true",
        help="Compare costs across all providers and exit"
    )
    parser.add_argument(
        "--validate-env",
        action="store_true",
        help="Validate environment variables and exit"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    return parser


def load_comments(args) -> List[str]:
    """Load comments based on command-line arguments."""
    if args.csv_file:
        print(f"📁 Loading comments from CSV file: {args.csv_file}")
        return DataLoader.load_from_csv(args.csv_file, args.csv_column)
    elif args.test_data:
        print(f"🧪 Loading {args.test_data} test data")
        return DataLoader.get_test_data(args.test_data)
    elif args.comments:
        print(f"📝 Loading {len(args.comments)} comments from command line")
        return DataLoader.load_from_list(args.comments)
    else:
        raise ValueError("No data source specified")


def generate_run_name(args, provider_name: str) -> str:
    """Generate a run name if not provided."""
    if args.run_name:
        return args.run_name
    
    # Auto-generate based on data source and provider
    if args.csv_file:
        base_name = os.path.splitext(os.path.basename(args.csv_file))[0]
    elif args.test_data:
        base_name = args.test_data
    else:
        base_name = "custom_comments"
    
    provider_suffix = "_openrouter" if args.provider == "openrouter" else "_openai"
    return f"{base_name}{provider_suffix}"


def compare_costs(comments: List[str]):
    """Compare costs across all providers."""
    print("💰 Comparing costs across providers...\n")
    
    cost_estimator = CostEstimator(Config.get_provider_config("openai"))  # Use any provider for comparison
    comparison = cost_estimator.compare_providers(comments)
    
    print(Formatter.format_provider_comparison(comparison))
    print("\n✅ Cost comparison completed")


def validate_environment():
    """Validate environment variables for all providers."""
    print("🔍 Validating environment variables...\n")
    
    all_valid = True
    for provider_key in Config.PROVIDERS:
        is_valid = Config.validate_environment(provider_key)
        status = "✅" if is_valid else "❌"
        provider_name = Config.get_provider_config(provider_key).name
        print(f"{status} {provider_name}: {'Valid' if is_valid else 'Invalid/Missing API key'}")
        if not is_valid:
            all_valid = False
    
    print(f"\n{'✅' if all_valid else '❌'} Environment validation {'passed' if all_valid else 'failed'}")
    return all_valid


def main():
    """Main entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    try:
        # Handle utility commands
        if args.validate_env:
            validate_environment()
            return
        
        # Load comments
        comments = load_comments(args)
        
        if args.compare_costs:
            compare_costs(comments)
            return
        
        # Validate provider environment
        if not Config.validate_environment(args.provider):
            print(f"❌ Environment validation failed for {args.provider}")
            print("Please set the required API key environment variable")
            return
        
        # Create provider
        print(f"🔧 Initializing {args.provider} provider...")
        provider = ProviderFactory.create_provider(args.provider)
        
        # Set up runtime configuration
        runtime_config = RuntimeConfig()
        runtime_config.set_provider(args.provider)
        runtime_config.exp_group = args.exp_group
        runtime_config.enable_wandb = not args.no_wandb
        runtime_config.enable_weave = not args.no_weave
        runtime_config.debug_mode = args.debug
        
        # Create logger
        logger = Logger(runtime_config)
        
        # Generate run name
        run_name = generate_run_name(args, provider.config.name)
        print(f"🏃 Run name: {run_name}")
        
        # Create and execute pipeline
        orchestrator = PipelineOrchestrator(provider, logger)
        report = orchestrator.execute_pipeline(comments, run_name)
        
        # Save structured JSON output to results folder
        if report.structured_json:
            import json
            import os
            
            # Ensure results directory exists
            os.makedirs("results", exist_ok=True)
            
            # Save structured JSON
            json_filename = f"results/{run_name}_structured_output.json"
            with open(json_filename, 'w') as f:
                json.dump(report.structured_json, f, indent=2)
            
            print(f"📄 Structured JSON saved to: {json_filename}")
        
        # Finish logging
        logger.finish()
        
        print(f"\n🎉 Pipeline completed successfully!")
        print(f"📊 Report available in W&B: {Config.WB_PROJECT_NAME}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 