# Evaluating ChatGPT as a Portfolio Decision-Maker in Microcap Equities

*An Exploratory, Forward-Only Paper Trading Study*

## Abstract

### TODO:

## Introduction

### TODO:

## Scope and Contribution

### TODO:

## Experimental Setup

### Human Input and Execution

Portfolio and trade log data were updated manually after each NYSE trading day using a standardized processing script, which generated a structured daily input summary (see Appendix [DAILY INPUT]). This summary was provided to the language model as the sole input for decision-making. If trade actions were requested, they were executed on the subsequent trading day. All market data were restricted to only regular trading hours; no pre-market or after-hours data were collected or used.

Human involvement was strictly limited to data entry and trade execution. No discretionary overrides or optimizations were applied to model-generated decisions.

On a limited number of occasions, daily updates could not be performed following market close. In these cases, the missed update was processed using only past data on that market day. To prevent lookahead bias, the model was explicitly constrained to rely solely on the provided input and was prohibited from accessing external or future information.

### Weekly Research Cycle and Execution Exceptions

A weekly research cycle was conducted on Fridays using a dedicated deep research prompt (see Appendix [DEEP RESEARCH PROMPT]) and the "Deep Research" feature was used. When using the "Deep Research" mode, the model will ask clarifing questions. When the model asked for trading guidance, no judgement was given, however questions regarding rules and constriants were always answered accurately. Any trade actions proposed outside this framework on Fridays were deferred pending inclusion in the weekly research output. The resulting report was archived, and all trade actions outlined were executed during the subsequent trading week.

This structure enforced a consistent separation between daily operational updates and higher-level strategic reassessment. Execution remained forward-only.


## Data Description

### Types of Data Collected

This dataset includes overall daily portfolio data for equity and cash, and also includes individual ticker data for each given data. Detailed portfolio CSV columns are provided in Appendix [TRADE LOG CSV DATA]. Trade logs were kept in the event of both buying and selling of securities. See Appendix [TRADE LOG CSV DATA] for detailed schema. Raw analytical reports generated during execution were archived in PDF format. Associated textual summaries were also recorded; however, neither the raw reports nor the summaries were incorporated into the analyses presented in this report.

### Granularity

All benchmark and portfolio data are recorded at daily frequency, with values reflecting end-of-day observations.

### Time Span

The experiment covers the period from July 27, 2025 to December 26, 2025, with all portfolio and benchmark data recorded within this timeframe.

## Methodology

### Research Design

This study employs a forward-looking, rule-based observational design with quasi-experimental controls.

### Decision-Making Framework

The large language model ChatGPT was used as a decision-making engine for the portfolio. The model was tasked with generating daily and weekly trade decisions based exclusively on structured summaries of portfolio state and market data.

No discretionary judgment was applied to model outputs. Human involvement was limited to prompting the model and executing requested trades exactly as the model instructed. The decision process was fully specified in advance and remained constant throughout the study period.

### Microcap Focus

The model was restricted to purchasing equities within the microcapitalization universe (market capitalization ≤ $300 million). This constraint was imposed to evaluate model behavior in securities characterized by limited institutional coverage and reduced analyst attention.

Given these conditions, the model’s reasoning was expected to rely primarily on publicly available disclosures, such as company press releases, and on information typically discussed in retail-focused analyses. This design choice allowed observation of the model’s decision-making processes in environments with sparse formal coverage and higher informational asymmetry.

### Data Sources and Information Constraints

Market data used for portfolio calculations, metrics, and summaries were sourced from Yahoo Finance and restricted to end-of-day observations during regular trading hours. These data were processed into standardized daily input summaries reflecting historical price information, portfolio holdings, and cash balances.

Although the research process permitted consultation of publicly available web sources for contextual analysis, the language model did not have direct access to external websites, raw market data feeds, or real-time information at decision time. Instead, the model operated exclusively on the structured summaries provided as input.

Weekly research reports and output summaries generated during the study were archived for documentation and analysis purposes. These materials were not incorporated into subsequent model inputs and did not influence future decision-making. Textual reports were not analyzed or used for the conclusions stated in this study.

All information supplied to the model was limited to data available as of the close of the relevant trading day. No future market data, post-close information, or subsequent outcomes were included in any model input.

### Bias Mitigation and Validity Controls

Multiple controls were implemented to mitigate common sources of bias in trading studies. To prevent lookahead bias, all model decisions were generated using only information available prior to trade execution, and all trades were executed on a forward-only basis.

Human involvement was strictly limited to data entry and execution of model-generated instructions. No discretionary overrides, trade filtering, or post hoc optimizations were applied at any point during the experimental period.

On occasions when daily data updates could not be performed immediately following market close, missed updates were processed using only information available as of that trading day. The model was explicitly constrained to rely solely on the provided historical inputs, ensuring that delayed data entry did not introduce access to future information.

Although prompt templates evolved over the course of the evaluation, all changes were limited to clarifying existing rules and improving the consistency and precision of report formatting. No changes were made to decision logic, constraints, or trade selection criteria.

## Performance Results

![](images/equity_vs_baseline.png)
**Figure 1.** Portfolio equity versus benchmark (normalized to $100) over time.

As shown in Figure 1, portfolio equity declined substantially relative to both the Russell 2000 and the S&P 500 over the experimental period.

![](images/equity_with_annotations.png)
**Figure 2.** Portfolio equity with max drawdown percentage (red) and largest run (green).

Figure 2 highlights the largest positive equity movement and the maximum drawdown observed during the experimental period. The largest run occurred between November 13, 2025 and November 18, 2025, during which portfolio equity increased by 21.51%. The maximum drawdown reached −50.33%, corresponding to an equity value of $67.10 on November 6, 2025.


## Trade-Level Analysis

### TODO:


Full Individual Trade Table found in Appendix[Individual Trade Table]

## Concentration and Risk Analysis

![](images/return_by_trades.png)
**Figure 3.** Realized PnL (USD) by ticker.

Figure 3 shows 10 of the 22 tickers the model bought within the experimental period generated profits.
Profits among tickers generally had concentrated profits; with the exception of ATYR,
losses were less concentrated. 

![](images/top_losses_vs_wins.png)
**Figure 4.** Top realized PnL (USD) ticker wins vs. losses.

As shown in Figure 4, losses were larger in magnitude than gains, with ATYR accounting for the most significant downside outcome.

These distributions indicate a highly concentrated return profile, with overall portfolio outcomes driven by a small number of large-magnitude trades rather than by broadly distributed incremental gains. Downside risk was similarly concentrated, with a limited number of positions accounting for a disproportionate share of total losses. As a result, aggregate performance was sensitive to individual trade outcomes.

Summary statistics reported in this section are derived from the Pure PnL tables provided in Appendix [Pure PnL Tables].

Calculated summary metrics further support the patterns observed in Figures 3 and 4; aggregate trade outcomes exhibited pronounced asymmetry. While average gains (6.11) and average losses (−6.15) were similar in magnitude, median losses (−2.61) were substantially smaller than median gains (4.97), indicating that downside performance was driven by a small number of large negative outcomes. This concentration is reflected in an overall profit factor of 0.83, consistent with losses outweighing gains over the experimental period.

Overall portfolio performance was therefore sensitive to a small number of extreme trade outcomes rather than to broadly distributed incremental returns.


## Behavioral Analysis

### TODO:

![](images/holding_distubution.png)
**Figure 6.** Distribution of holding periods across individual closed trades.

![](images/repeated_exposure.png)
**Figure 7.** Number of buy-side trade entries per ticker.

## Operational Constraints and Failure Modes

### TODO:

## Discussion

### TODO:

## Limitations

### TODO:

## Conclusion

### TODO:

## Future Work

### TODO:

## Appendix A. Metric Definitions and Formulas

## Appendix B. Representative LLM Outputs

## Appendix C. Prompt Templates and Versions

## Appendix D. Additional Tables and Figures
