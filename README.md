# T3C Pipeline - Python Implementation

A Python implementation of the Talk to the City (T3C) pipeline for analyzing and organizing diverse human perspectives from comments and text data.

## What it does

The T3C pipeline processes comments through these steps:
1. **Taxonomy Creation** - Organize comments into topics and subtopics
2. **Claims Extraction** - Extract specific claims from each comment  
3. **Sorting** - Sort topics by frequency
4. **Deduplication** - Remove duplicate claims within topics
5. **JSON Output** - Generate structured T3C format

## Quick Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set API key (choose one):
```bash
# OpenRouter (recommended - cheaper)
export OPENROUTER_API_KEY="sk-or-your-openrouter-key"

# Or OpenAI
export OPENAI_API_KEY="sk-your-openai-key"
```

## Usage Examples

### Test with built-in data
```bash
python main.py --test-data scifi --provider openrouter --run-name "my_test"
```

### Process CSV file
```bash
python main.py --csv-file your_data.csv --provider openrouter --run-name "csv_analysis"
```

### Process custom comments
```bash
python main.py --comments "I love AI" "AI is scary" "AI will help humanity" --provider openrouter
```

### Compare costs between providers
```bash
python main.py --test-data scifi --compare-costs
```

## Configuration

**Providers:**
- `openrouter` (default) - Uses Gemini 2.0 Flash (~92% cheaper than OpenAI)
- `openai` - Uses GPT-4 Turbo

**Data Sources:**
- `--test-data {scifi,pets}` - Built-in test datasets
- `--csv-file PATH` - CSV file with comments
- `--comments TEXT [TEXT ...]` - Direct comment input

**Options:**
- `--run-name NAME` - Name for the analysis run
- `--csv-column COLUMN` - Column name in CSV (default: "comment")
- `--no-wandb` - Disable W&B logging
- `--debug` - Enable debug mode

## Output

The pipeline generates:
- **Console output**: Real-time progress and results
- **JSON file**: `results/{run_name}_structured_output.json`
- **W&B dashboard**: Comprehensive metrics and visualization
- **Cost tracking**: Detailed cost breakdown

## Known Issues

⚠️ **JSON Formatting**: The structured JSON output doesn't fully match the expected T3C format yet. UUIDs are now properly generated in Python, but the overall structure may need refinement for full compatibility with T3C visualization tools.

## Cost Comparison

- **OpenRouter (Gemini 2.0 Flash)**: ~$0.01 for 10 comments
- **OpenAI (GPT-4 Turbo)**: ~$0.12 for 10 comments
- **Savings**: ~92% cheaper with OpenRouter

## Environment Validation

Check if your API keys are working:
```bash
python main.py --test-data scifi --validate-env
```

## Sample Output Structure

```json
{
  "data": [
    "v0.2",
    {
      "title": "my_analysis",
      "description": "T3C Pipeline Analysis Results",
      "topics": [
        {
          "id": "uuid",
          "title": "Theme Name",
          "subtopics": [
            {
              "id": "uuid",
              "title": "Topic Name", 
              "claims": [
                {
                  "id": "uuid",
                  "title": "Claim Title",
                  "quotes": [
                    {
                      "id": "uuid",
                      "text": "Original comment text",
                      "reference": {
                        "interview": "Anonymous #1",
                        "data": ["text", {"startIdx": 0, "endIdx": 25}]
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Troubleshooting

**API Key Issues:**
```bash
python main.py --test-data scifi --validate-env
```

**CSV Column Not Found:**
```bash
python main.py --csv-file data.csv --csv-column "your_column_name"
```

**Missing Dependencies:**
```bash
pip install -r requirements.txt
```

## Contributing

This project is part of the DeepGov LLM Pipeline suite. The pipeline is designed to be extensible - you can add new providers, data sources, or modify the processing steps as needed. 