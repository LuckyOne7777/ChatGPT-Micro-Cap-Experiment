# Start Your Own

This folder lets you run the trading experiment on your own computer. It contains two small scripts and the CSV files they produce.

Run the commands below from the repository root. The scripts automatically
save their CSV data inside this folder.

## Overview

 **Install dependencies:**
   ```bash
   # Recommended: Use a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   pip install -r requirements.txt
   ```

**Processing Portfolio:**
   ```bash
   # ALWAYS include a CSV file of history
   python trading_script.py --file "Start Your Own/chatgpt_portfolio_update.csv"
   ```

**To Save Prior Days:**
   ```bash

   # Save data with specific date
   python trading_script.py --asof 2025-08-27 --file "Start Your Own/chatgpt_portfolio_update.csv"
   ```

**Generate performance graphs:**
   ```bash
   python "Start Your Own/Generate_Graph.py"
   ```

### Argument Table for 'Generate_Graph.py'

| Argument            | Type   | Default          | Description                                                        |
|---------------------|--------|------------|--------------------------------------------------------------------------|
| `--start-date`      | str    | Start date in CSV| Start date in `YYYY-MM-DD` format                                  |
| `--end-date`        | str    | End date in CSV| End date in `YYYY-MM-DD` format                                      |
| `--start-equity`    | float  | 100.0   | Baseline to index both series (default 100)                                 |
| `--baseline-file`   | str    | —       | Path to a text file containing a single number for baseline                 |
| `--output`          | str    | —       | Optional path to save the chart (`.png` / `.jpg` / `.pdf`)                  |

## ProcessPortfolio.py

This script updates your portfolio and logs trades.

**NOTE: ALWAYS RUN PROGRAM AFTER TRADING DAYS, OR YESTERDAY'S DATA WILL BE USED.**

**Follow the prompts**
   - The program uses past data from 'chatgpt_portfolio_update.csv' to automatically grab today's portfolio.
   - If 'chatgpt_portfolio_update.csv' is empty (meaning no past trading days logged), you will required to enter your starting cash.
   - From here, you can set up your portfolio or make any changes.
   - The script asks if you want to record manual buys or sells.
   - After you hit 'Enter' all calculations for the day are made.
   - Results are saved to `chatgpt_portfolio_update.csv` and any trades are added to `chatgpt_trade_log.csv`.
   - In the terminal, daily results are printed. Copy and paste results into the LLM. **ALL PROMPTING IS MANUAL AT THE MOMENT.**

## Generate_Graph.py

This script draws a graph of your portfolio versus the S&P 500.

**Program will ALWAYS use 'Start Your Own/chatgpt_portfolio_update.csv' for data.**

1. **Ensure you have portfolio data**
   - Run `ProcessPortfolio.py` at least once so `chatgpt_portfolio_update.csv` has data.
2. **Run the graph script**
   ```bash
   python "Start Your Own/Generate_Graph.py" --start-equity 100
   ```
   
3. **View the chart**
   - A window opens showing your portfolio value vs. S&P 500. Results will be adjusted for baseline equity.

All of this is still VERY NEW, so there is bugs. Please reach out if you find an issue or have a question.

Both scripts are designed for beginners, feel free to experiment and modify them as you learn.
