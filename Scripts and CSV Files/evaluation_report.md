# Evaluating ChatGPT as a Portfolio Decision-Maker in Microcap Equities

*An Exploratory, Forward-Only Paper Trading Study*

## Abstract

## Introduction

## Scope and Contribution

## Experimental Setup

## Data Description

### Types of Data Collected

This dataset includes overall daily portfolio data for equity and cash, and also includes individual ticker data for each given data. Detailed portfolio CSV columns are provided in Appendix [TRADE LOG CSV DATA]. Trade logs were kept in the event of both buying and selling of securities. See Appendix [TRADE LOG CSV DATA] for detailed schema. Raw analytical reports generated during execution were archived in PDF format. Associated textual summaries were also recorded; however, neither the raw reports nor the summaries were incorporated into the analyses presented in this report.

### Granularity

All benchmark and portfolio data are recorded at daily frequency, with values reflecting end-of-day observations.

### Time Span

The experiment covers the period from July 27, 2025 to December 26, 2025, with all portfolio and benchmark data recorded within this timeframe.

## Methodology

### Human Input and Execution

Portfolio and trade log data were updated manually after each NYSE trading day using a standardized processing script, which generated a structured daily input summary (see Appendix [DAILY INPUT]). This summary was provided to the language model as the sole input for decision-making. If trade actions were requested, they were executed on the subsequent trading day. All market data were restricted to only regular trading hours; no pre-market or after-hours data were collected or used.

Human involvement was strictly limited to data entry and trade execution. No discretionary overrides or optimizations were applied to model-generated decisions.

On a limited number of occasions, daily updates could not be performed following market close. In these cases, the missed update was processed using only past data on that market day. To prevent lookahead bias, the model was explicitly constrained to rely solely on the provided input and was prohibited from accessing external or future information.

### Weekly Research Cycle and Execution Exceptions

A weekly research cycle was conducted on Fridays using a dedicated deep research prompt (see Appendix [DEEP RESEARCH PROMPT]) and the "Deep Research" feature was used. When using the "Deep Research" mode, the model will ask clarifing questions. When the model asked for trading guidance, no judgement was given, however questions regarding rules and constriants were always answered accurately. Any trade actions proposed outside this framework on Fridays were deferred pending inclusion in the weekly research output. The resulting report was archived, and all trade actions outlined were executed during the subsequent trading week.

This structure enforced a consistent separation between daily operational updates and higher-level strategic reassessment. All execution remained forward-only.

## Performance Results

![](images/equity_vs_baseline.png)
**Figure 1.** Portfolio equity versus benchmark (normalized to $100) over time.

As shown in Figure 1, portfolio equity declined substantially relative to both the Russell 2000 and the S&P 500 over the experimental period.

![](images/equity_with_annotations.png)
**Figure 2.** Portfolio equity with max drawdown percentage (red) and largest run (green).

Figure 2 highlights the largest positive equity movement and the maximum drawdown observed during the experimental period. The largest run occurred between November 13, 2025 and November 18, 2025, during which portfolio equity increased by 21.51%. The maximum drawdown reached −50.33%, corresponding to an equity value of $67.10 on November 6, 2025.


## Trade-Level Analysis



Full Individual Trade Table found in Appendix[Individual Trade Table]

## Concentration and Risk Analysis

Full Pure PnL Tables found in Appendix[Pure PnL Tables]

![](images/return_by_trades.png)
**Figure 3.** Realized PnL (USD) by ticker.

![](images/top_losses_vs_wins.png)
**Figure 4.**

## Behavioral Analysis

![](images/holding_distubution.png)
**Figure 6.** Distribution of holding periods across individual closed trades.

![](images/repeated_exposure.png)
**Figure 7.** Number of buy-side trade entries per ticker.

## Operational Constraints and Failure Modes

## Discussion

## Limitations

## Conclusion

## Future Work

## Appendix A. Metric Definitions and Formulas

## Appendix B. Representative LLM Outputs

## Appendix C. Prompt Templates and Versions

## Appendix D. Additional Tables and Figures
