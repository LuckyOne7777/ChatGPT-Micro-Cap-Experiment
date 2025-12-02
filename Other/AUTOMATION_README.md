# Automated Trading System

This system automates the ChatGPT Micro-Cap trading experiment by integrating LLM APIs to generate trading decisions automatically.

## Features

- **Automated Prompt Generation**: Creates daily trading prompts with current portfolio data
- **LLM Integration**: Supports OpenAI GPT API
- **Trade Execution**: Parses LLM responses and executes recommended trades
- **Risk Management**: Includes confidence thresholds and dry-run modes
- **Logging**: Saves all LLM responses and trading decisions

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install openai
```

### 2. Get API Key

- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### 3. Set Environment Variable

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"
```

## Usage

The `simple_automation.py` script provides automated trading decisions:

```bash
# Basic usage with OpenAI
python simple_automation.py --api-key YOUR_OPENAI_KEY

# Using environment variable
export OPENAI_API_KEY="your-key"
python simple_automation.py

# Dry run (no actual trades executed)
python simple_automation.py --dry-run

# Custom model
python simple_automation.py --model gpt-3.5-turbo
```

## How It Works

### 1. Portfolio Analysis
- Loads current portfolio state from CSV files
- Calculates cash balance and total equity
- Formats holdings data for LLM consumption

### 2. Prompt Generation
- Creates structured prompts with portfolio data
- Includes trading rules and constraints
- Requests JSON-formatted responses

### 3. LLM Processing
- Sends prompts to chosen LLM API
- Receives trading recommendations
- Parses JSON responses for trade details

### 4. Trade Execution
- Validates trade recommendations
- Checks cash availability and position limits
- Executes approved trades (or logs in dry-run mode)

## Configuration

### LLM Settings
- **Temperature**: 0.3 (lower for more consistent decisions)
- **Max Tokens**: 1500-2000 (adjust based on model)
- **Model**: GPT-4 recommended for best results

### Trading Rules
- Maximum position size: 10% of portfolio
- Minimum confidence threshold: 70%
- Cash reserve: Minimum $500
- Micro-cap focus: <$300M market cap

## Output Files

### LLM Responses
- `llm_responses.jsonl`: All LLM interactions and responses
- `automated_trades.jsonl`: All automated trading decisions

### Portfolio Updates
- Uses existing CSV files from the original trading script
- Maintains compatibility with manual trading system

## Safety Features

### Dry Run Mode
Always test with `--dry-run` first to see what trades would be executed:

```bash
python simple_automation.py --dry-run
```

### Confidence Thresholds
The system includes confidence scoring to avoid low-quality recommendations.

### Error Handling
- Graceful handling of API failures
- JSON parsing error recovery
- Invalid trade validation

## Integration with Existing System

The automation system is designed to work alongside the existing manual trading system:

1. **Same Data Files**: Uses the same CSV files as the manual system
2. **Compatible Format**: Maintains the same portfolio and trade log formats
3. **Fallback Support**: Can switch between automated and manual modes

## Example Workflow

```bash
# 1. Test the system with dry run
python simple_automation.py --dry-run

# 2. Run automated trading
python simple_automation.py

# 3. Review results
cat "Start Your Own/llm_responses.jsonl" | tail -1

# 4. Check portfolio updates
python "Start Your Own/Trading_Script.py"
```

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```bash
   export OPENAI_API_KEY="your-key"
   ```

2. **JSON Parsing Errors**
   - Check LLM response format
   - Verify model supports structured output
   - Try different temperature settings

3. **Trade Execution Failures**
   - Check cash availability
   - Verify ticker symbols
   - Review position size limits

### Debug Mode

Add verbose logging by modifying the scripts to print more details about the LLM interactions.

## Customization

### Custom Prompts
Modify the `generate_trading_prompt()` function to customize the prompts sent to the LLM.

### Different Models
Experiment with different models:
- `gpt-4`: Best performance, higher cost
- `gpt-3.5-turbo`: Good performance, lower cost

### Trading Rules
Adjust risk parameters in the configuration or modify the validation logic.

## Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Consider rate limiting for API calls
- Monitor API usage and costs

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the LLM response logs
3. Test with dry-run mode first
4. Verify API key permissions and quotas