"""
Simple Automation Script for ChatGPT Micro-Cap Trading

This script integrates with the existing trading_script.py to provide
automated LLM-based trading decisions for micro-cap stocks.

Usage:
    python simple_automation.py --api-key YOUR_KEY [--dry-run]
"""

import json
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd

# Import existing trading functions
from trading_script import (
    process_portfolio,
    daily_results,
    load_latest_portfolio_state,
    set_data_dir,
    PORTFOLIO_CSV,
    TRADE_LOG_CSV,
    last_trading_date
)

# Optional OpenAI integration
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def generate_trading_prompt(portfolio_df: pd.DataFrame, cash: float, total_equity: float) -> str:
    """
    Generate a detailed trading prompt for the LLM based on current portfolio state.

    Args:
        portfolio_df (pd.DataFrame): Current portfolio holdings.
        cash (float): Available cash.
        total_equity (float): Total portfolio value including holdings.

    Returns:
        str: Formatted prompt for LLM.
    """
    holdings_text = portfolio_df.to_string(index=False) if not portfolio_df.empty else "No current holdings"
    today = last_trading_date().date().isoformat()

    prompt = f"""You are a professional portfolio analyst. Here is your current portfolio state as of {today}:

[ Holdings ]
{holdings_text}

[ Snapshot ]
Cash Balance: ${cash:,.2f}
Total Equity: ${total_equity:,.2f}

Rules:
- You have ${cash:,.2f} in cash available for new positions
- Prefer U.S. micro-cap stocks (<$300M market cap)
- Full shares only, no options or derivatives
- Use stop-losses for risk management
- Be conservative with position sizing

Analyze the current market conditions and provide specific trading recommendations.

Respond with ONLY a JSON object in this exact format:
{{
    "analysis": "Brief market analysis",
    "trades": [
        {{
            "action": "buy",
            "ticker": "SYMBOL",
            "shares": 100,
            "price": 25.50,
            "stop_loss": 20.00,
            "reason": "Brief rationale"
        }}
    ],
    "confidence": 0.8
}}

Only recommend trades you are confident about. If no trades are recommended, use an empty trades array."""
    
    return prompt


def call_openai_api(prompt: str, api_key: str, model: str = "gpt-4") -> str:
    """
    Call OpenAI API with the trading prompt and return the response.

    Args:
        prompt (str): Trading prompt.
        api_key (str): OpenAI API key.
        model (str): OpenAI model to use (default: "gpt-4").

    Returns:
        str: LLM response content or error message.
    """
    if not HAS_OPENAI:
        raise ImportError("openai package not installed. Run: pip install openai")

    client = openai.OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional portfolio analyst. Always respond with valid JSON in the exact format requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"API call failed: {e}"})


def parse_llm_response(response: str) -> Dict[str, Any]:
    """
    Parse LLM response and extract trading decisions.

    Args:
        response (str): Raw LLM response.

    Returns:
        Dict[str, Any]: Parsed JSON response or error dictionary.
    """
    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        json_str = json_match.group() if json_match else response
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}\nRaw response: {response}")
        return {"error": "Failed to parse response", "raw_response": response}


def execute_automated_trades(
    trades: List[Dict[str, Any]],
    portfolio_df: pd.DataFrame,
    cash: float
) -> Tuple[pd.DataFrame, float]:
    """
    Execute or simulate trades recommended by LLM.

    Args:
        trades (List[Dict[str, Any]]): List of trade instructions.
        portfolio_df (pd.DataFrame): Current portfolio holdings.
        cash (float): Available cash.

    Returns:
        Tuple[pd.DataFrame, float]: Updated portfolio and cash balance.
    """
    print(f"\n=== Executing {len(trades)} LLM-recommended trades ===")

    for trade in trades:
        action = trade.get('action', '').lower()
        ticker = trade.get('ticker', '').upper()
        shares = float(trade.get('shares', 0))
        price = float(trade.get('price', 0))
        stop_loss = float(trade.get('stop_loss', 0))
        reason = trade.get('reason', 'LLM recommendation')

        if action == 'buy' and shares > 0 and price > 0 and ticker:
            cost = shares * price
            if cost <= cash:
                print(f"BUY: {shares} shares of {ticker} at ${price:.2f} (stop: ${stop_loss:.2f}) - {reason}")
                cash -= cost
                print(f"  Simulated: Cash reduced by ${cost:.2f}, new balance: ${cash:.2f}")
            else:
                print(f"BUY REJECTED: {ticker} - Insufficient cash (need ${cost:.2f}, have ${cash:.2f})")
        elif action == 'sell' and shares > 0 and price > 0 and ticker:
            proceeds = shares * price
            print(f"SELL: {shares} shares of {ticker} at ${price:.2f} - {reason}")
            cash += proceeds
            print(f"  Simulated: Cash increased by ${proceeds:.2f}, new balance: ${cash:.2f}")
        elif action == 'hold':
            print(f"HOLD: {ticker} - {reason}")
        else:
            print(f"INVALID/UNKNOWN ACTION: {action} for {ticker} ({trade})")

    return portfolio_df, cash


def run_automated_trading(
    api_key: str,
    model: str = "gpt-4",
    data_dir: str = "Start Your Own",
    dry_run: bool = False
):
    """Run the full automated trading process."""
    print("=== Automated Trading System ===")

    data_path = Path(data_dir)
    set_data_dir(data_path)

    # Load or initialize portfolio
    portfolio_file = data_path / "chatgpt_portfolio_update.csv"
    if portfolio_file.exists():
        portfolio_df, cash = load_latest_portfolio_state(str(portfolio_file))
    else:
        portfolio_df = pd.DataFrame(columns=["ticker", "shares", "stop_loss", "buy_price", "cost_basis"])
        cash = 10000.0

    total_value = portfolio_df['cost_basis'].sum() if not portfolio_df.empty and 'cost_basis' in portfolio_df.columns else 0.0
    total_equity = cash + total_value
    print(f"Portfolio loaded: ${cash:,.2f} cash, ${total_equity:,.2f} total equity")

    # Generate prompt
    prompt = generate_trading_prompt(portfolio_df, cash, total_equity)
    print(f"\nGenerated prompt ({len(prompt)} characters)")

    # Call LLM
    print("Calling LLM for trading recommendations...")
    response = call_openai_api(prompt, api_key, model)
    print(f"Received response ({len(response)} characters)")

    parsed_response = parse_llm_response(response)
    if "error" in parsed_response:
        print(f"Error: {parsed_response['error']}")
        return

    analysis = parsed_response.get('analysis', 'No analysis provided')
    confidence = parsed_response.get('confidence', 0.0)
    trades = parsed_response.get('trades', [])

    print(f"\n=== LLM Analysis ===")
    print(f"Analysis: {analysis}")
    print(f"Confidence: {confidence:.1%}")
    print(f"Recommended trades: {len(trades)}")

    # Execute trades or dry-run
    if trades:
        if dry_run:
            print(f"\n=== DRY RUN - Would execute {len(trades)} trades ===")
            for trade in trades:
                print(f"  {trade.get('action', 'unknown').upper()}: {trade.get('shares', 0)} shares of {trade.get('ticker', 'unknown')} at ${trade.get('price', 0):.2f}")
        else:
            portfolio_df, cash = execute_automated_trades(trades, portfolio_df, cash)
    else:
        print("No trades recommended")

    # Save response
    response_file = data_path / "llm_responses.jsonl"
    with open(response_file, "a") as f:
        f.write(json.dumps({
            "timestamp": pd.Timestamp.now().isoformat(),
            "response": parsed_response,
            "raw_response": response
        }) + "\n")

    print(f"\n=== Analysis Complete ===")
    print(f"Response saved to: {response_file}")


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Simple Automated Trading")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--data-dir", default="Start Your Own", help="Data directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute trades, just show recommendations")

    args = parser.parse_args()

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key required. Set OPENAI_API_KEY env var or use --api-key")
        return

    run_automated_trading(
        api_key=api_key,
        model=args.model,
        data_dir=args.data_dir,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
