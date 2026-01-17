import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Load and prepare data
# -----------------------------

df = pd.read_csv("Scripts and CSV Files/Daily Updates.csv")
df = df[df["Ticker"] != "TOTAL"]

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values(["Ticker", "Date"])

# -----------------------------
# Identify trade episodes
# -----------------------------

df["in_position"] = df["Shares"] > 0
df["prev_in_position"] = (
    df.groupby("Ticker")["in_position"]
      .shift(1, fill_value=False)
)

df["episode_start"] = df["in_position"] & (~df["prev_in_position"])

# Assign episode IDs per ticker
df["episode_id"] = (
    df.groupby("Ticker")["episode_start"]
      .cumsum()
)

# Keep only days where a position is held
episodes = df[df["in_position"]].copy()

# -----------------------------
# Compute episode-level metrics
# -----------------------------

episode_stats = (
    episodes
    .groupby(["Ticker", "episode_id"])
    .agg(
        start_date=("Date", "first"),
        end_date=("Date", "last"),
        peak_pnl=("PnL", "max"),
        exit_pnl=("PnL", "last"),
        duration_days=("Date", lambda x: (x.max() - x.min()).days)
    )
    .reset_index()
)

# -----------------------------
# Peak Capture Ratio (decision-level)
# -----------------------------

episode_stats["peak_capture_ratio"] = (
    episode_stats["exit_pnl"] / episode_stats["peak_pnl"]
)

# Remove undefined / meaningless ratios
episode_stats.loc[
    episode_stats["peak_pnl"] <= 0,
    "peak_capture_ratio"
] = pd.NA
episode_stats = episode_stats.drop("episode_id", axis=1)


plt.scatter(
    episode_stats["peak_pnl"],
    episode_stats["peak_capture_ratio"]
)

plt.axhline(1.0, linestyle="--", linewidth=1, alpha=0.7)
plt.axhline(0.0, linestyle="--", linewidth=1, alpha=0.7)

plt.xlabel("Peak Unrealized PnL (USD)")
plt.ylabel("Peak Capture Ratio (Exit / Peak)")
plt.ylim(-1.5, 1.2)

outlier = episode_stats.loc[
    episode_stats["peak_capture_ratio"].idxmin()
]

plt.title("Exit Timing Relative to Peak Unrealized Profit")

plt.savefig(
    "Scripts and CSV Files/images/episode_pcr_scatter.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
