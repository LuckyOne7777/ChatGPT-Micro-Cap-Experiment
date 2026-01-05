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



### trading_script.py


### Arguement Table for `trading_script.py`

| Argument            | Short | Default | Choices                               | Description                                   |
|---------------------|-------|---------|---------------------------------------|-----------------------------------------------|
| `--data-dir`        |       | None    |                                       | REQUIRED data directory                       |
| `--asof`            |       | None    |                                       | Treat this YYYY-MM-DD as "today"              |
| `--log-level`       |       | None    | DEBUG, INFO, WARNING, ERROR, CRITICAL | Set the logging level (default: none)         |
| `--starting-equity` | `-s`  | None    |                                       | Optional starting equity (cash amount)        |

### Examples
- Data directory is required to run:  
  `python trading_script.py --data-dir "Start Your Own"`

- Run as if today were 2025-10-01:  
  `python trading_script.py --data-dir "Start Your Own" --asof 2025-10-01`

- Run with detailed logging enabled:  
  `python trading_script.py --data-dir "Start Your Own" --log-level DEBUG`

- Run with starting equity of $10,000:  
  `python trading_script.py --data-dir "Start Your Own" --starting-equity 10000`

- Combine multiple options:  
  `python trading_script.py --data-dir "Start Your Own" --asof 2025-10-01 --log-level INFO -s 5000`

### `Start Your Own/ProcessPortfolio.py`

Simply a wrapper for `trading_script.py`. Will automatically use 'Start Your Own' as a data directory. However, it does not support other 

**Generating Graphs:**

**Program will ALWAYS use 'Start Your Own/chatgpt_portfolio_update.csv' for data.**

1. **Ensure you have portfolio data**
   - Run `ProcessPortfolio.py` at least once so `chatgpt_portfolio_update.csv` has data.

   ```bash
   python "Start Your Own/Generate_Graph.py"
   ```

### Argument Table for 'Generate_Graph.py'

| Argument            | Type   | Default          | Description                                                        |
|---------------------|--------|------------|--------------------------------------------------------------------------|
| `--start-date`      | str    | Start date in CSV| Start date in `YYYY-MM-DD` format                                  |
| `--end-date`        | str    | End date in CSV| End date in `YYYY-MM-DD` format                                      |
| `--start-equity`    | float  | 100.0   | Baseline to index both series (default 100)                                 |
| `--output`          | str    | —       | Optional path to save the chart (`.png` / `.jpg` / `.pdf`)                  |

### IMPORTANT

Always run the program after the market closes at 4:00 PM EST, otherwise it will default to using the previous day’s data.

Because the program relies on past data, orders for a given day are generated after that day’s trading session and must be placed on the following trading day. This prevents lookahead bias. For example, When I receive orders from ChatGPT, I run the program and input the orders the close the day after.  

**Information**
   - The program uses past data from 'chatgpt_portfolio_update.csv' to automatically grab today's portfolio.
   - If 'chatgpt_portfolio_update.csv' is empty (meaning no past trading days logged), you will required to enter your starting cash.
   - From here, you can set up your portfolio or make any changes.
   - The script asks if you want to record manual buys or sells.
   - After you hit 'Enter' all calculations for the day are made.
   - Results are saved to `chatgpt_portfolio_update.csv` and any trades are added to `chatgpt_trade_log.csv`.
   - In the terminal, daily results are printed. Copy and paste results into the LLM.
To automate prompts, check out the [Automation Guide](https://github.com/LuckyOne7777/ChatGPT-Micro-Cap-Experiment/blob/main/Other/AUTOMATION_README.md)

All of this is still VERY NEW, so there are bugs. Please reach out if you find an issue or have a question.

Both scripts are designed for beginners, feel free to experiment and modify them as you learn.