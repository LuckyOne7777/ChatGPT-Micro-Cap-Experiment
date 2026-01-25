import matplotlib.pyplot as plt
import pandas as pd
from data_helper import assemble_path, DAILY_PATH

df = pd.read_csv(DAILY_PATH)
df = df[df["Ticker"] != "TOTAL"]

highest_pnl = df.groupby("Ticker")["PnL"].max()

plt.bar(highest_pnl.index, highest_pnl.values)
plt.ylabel("Peak Observed PnL (USD)")
plt.title("Highest Observed PnL by Ticker")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(
    assemble_path("highest_ticker_pnl.png"),
    dpi=300,
    bbox_inches="tight"
)
plt.show()
