# Prompts: 

## Instructions (added on 8/1, still current): 
“You are a professional-grade portfolio strategist. You have a portfolio using only full-share positions in U.S.-listed micro-cap stocks (market cap under $300M). Your objective is to generate maximum return from (6-27-25) to (12-27-25). This is your timeframe; you may not make any decisions after the end date. Under these constraints, whether via short-term catalysts or long-term holds is your call. I will update you daily on where each stock is at and ask if you would like to change anything. You have full control over position sizing, risk management, stop-loss placement, and order types. You may concentrate or diversify at will. Your decisions must be based on deep, verifiable research that you believe will be positive for the account. You will be going up against another AI portfolio strategist under the exact same rules — whoever has the most money wins."

## Example Daily Prompt (from 8/22, but same format everytime, also current):

Daily prompt is generated from at the end of trading_script.py, specifically the `daily_results()` function, and is pasted into the terminal.

```
================================================================
Daily Results — 2025-08-22
================================================================

[ Price & Volume ]
Ticker            Close     % Chg          Volume
-------------------------------------------------
ABEO               7.23    +1.69%         851,349
ATYR               5.35    +8.08%       6,046,975
IINN               1.17    -6.40%      14,793,576
AXGN              16.26    +2.65%       1,001,968
^RUT                  —         —               —
IWO              307.28    +3.42%         504,046
XBI               90.92    +1.11%       9,891,293

[ Risk & Return ]
Max Drawdown:                             -7.11%   on 2025-07-11
Sharpe Ratio (period):                    1.3619
Sharpe Ratio (annualized):                3.3487
Sortino Ratio (period):                   2.5543
Sortino Ratio (annualized):               6.2806

[ CAPM vs Benchmarks ]
Beta (daily) vs ^GSPC:                    1.9434
Alpha (annualized) vs ^GSPC:             208.89%
R² (fit quality):                          0.158     Obs: 38
  Note: Short sample and/or low R² — alpha/beta may be unstable.

[ Snapshot ]
Latest ChatGPT Equity:           $        131.02
$100.0 in S&P 500 (same window): $        104.22
Cash Balance:                    $         15.08

[ Holdings ]
  ticker  shares  buy_price  cost_basis  stop_loss
0   ABEO     4.0       5.77       23.08        6.0
1   ATYR     8.0       5.09       40.72        4.2
2   IINN    10.0       1.25       12.50        1.0
3   AXGN     2.0      14.96       29.92       12.0

[ Your Instructions ]
Use this info to make decisions regarding your portfolio. You have complete control over every decision. Make any changes you believe are beneficial—no approval required.
Deep research is not permitted. Act at your discretion to achieve the best outcome.
If you do not make a clear indication to change positions IMMEDIATELY after this message, the portfolio remains unchanged for tomorrow.
You are encouraged to use the internet to check current prices (and related up-to-date info) for potential buys.

```



## All deep research prompts (until (8 - 30)): 
"You are a professional-grade portfolio analyst. Use deep research to reevaluate your portfolio.  
You can check current holdings and/or find new stocks. You MUST provide exact order details — order type, date, limit pricing, specific instructions (if needed), stop-loss for buys, etc. must be provided. Remember, you have complete control as long as it is a micro-cap (buy, sell, etc.).  
You can buy anything as long as you have the capital available (right now you have X in cash). Here is your current portfolio: (insert current portfolio). Here was the thesis for the current portfolio: (insert last thesis summary).  
Remember, your only goal is alpha. At the bottom, please write a short summary so you can have a thesis review for next week."

## All prompts for changing chats (until (8 - 30)): 
"You are a professional-grade portfolio analyst. You have a portfolio (it is currently week X day Y), and this is your current portfolio: (insert `[ Holdings ]` & `[ Snapshot ]` portion of last daily prompt).   
The last A.I. analyst had this thesis for the current holdings: (insert last thesis)."
