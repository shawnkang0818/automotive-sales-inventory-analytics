import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(
    "data/processed/monthly_automotive_master.csv",
    parse_dates=["observation_date"]
)

print(df.columns)

recent = df[df["observation_date"] >= "2024-01-01"]

plt.figure(figsize=(12, 6))

plt.plot(
    recent["observation_date"],
    recent["sales_yoy_pct"],
    label="Sales YoY Growth"
)

plt.plot(
    recent["observation_date"],
    recent["inventory_yoy_pct"],
    label="Inventory YoY Growth"
)

plt.axhline(0, linewidth=1)

plt.title("Automotive Dealer Sales vs Inventory Growth")
plt.xlabel("Date")
plt.ylabel("Year-over-Year Growth (%)")
plt.legend()

plt.tight_layout()

plt.savefig(
    "dashboard/sales_vs_inventory_growth.png",
    dpi=300
)

plt.show()

plt.figure(figsize=(12, 6))

plt.plot(
    recent["observation_date"],
    recent["inventory_growth_gap"],
    label="Inventory Growth Gap"
)

plt.axhline(0, linewidth=1)

plt.title("Inventory Growth Gap")
plt.xlabel("Date")
plt.ylabel("Inventory YoY Growth - Sales YoY Growth (Percentage Points)")
plt.legend()

plt.tight_layout()

plt.savefig(
    "dashboard/inventory_growth_gap.png",
    dpi=300
)

plt.show()

positive_gap_months = recent[recent["inventory_growth_gap"] > 0]

print("\nMonths with inventory growth above sales growth:")
print(
    positive_gap_months[
        [
            "observation_date",
            "sales_yoy_pct",
            "inventory_yoy_pct",
            "inventory_growth_gap"
        ]
    ]
    .round(2)
    .to_string(index=False)
)

positive_gap_share = (
    (recent["inventory_growth_gap"] > 0).mean() * 100
)

print(
    "\nShare of months with positive inventory growth gap:",
    round(positive_gap_share, 1),
    "%"
)