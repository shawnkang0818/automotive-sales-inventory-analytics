import sqlite3

import pandas as pd


# --------------------------------------------------
# File paths
# --------------------------------------------------

operations_path = (
    "data/synthetic/synthetic_operations.csv"
)

forecast_backtest_path = (
    "data/processed/forecast_rolling_backtest.csv"
)

forecast_comparison_path = (
    "data/processed/forecast_model_comparison.csv"
)

database_path = (
    "data/processed/automotive_analytics.db"
)


# --------------------------------------------------
# Load CSV files
# --------------------------------------------------

operations_df = pd.read_csv(
    operations_path
)

forecast_backtest_df = pd.read_csv(
    forecast_backtest_path
)

forecast_comparison_df = pd.read_csv(
    forecast_comparison_path
)


# --------------------------------------------------
# Connect to SQLite database
# --------------------------------------------------

# sqlite3.connect() creates the database file
# automatically if it does not already exist.
connection = sqlite3.connect(
    database_path
)


# --------------------------------------------------
# Load DataFrames into SQL tables
# --------------------------------------------------

operations_df.to_sql(
    "operations",
    connection,
    if_exists="replace",
    index=False
)

forecast_backtest_df.to_sql(
    "forecast_backtest",
    connection,
    if_exists="replace",
    index=False
)

forecast_comparison_df.to_sql(
    "forecast_model_comparison",
    connection,
    if_exists="replace",
    index=False
)


# --------------------------------------------------
# Verify tables
# --------------------------------------------------

tables_query = """
SELECT name
FROM sqlite_master
WHERE type = 'table'
ORDER BY name;
"""

tables = pd.read_sql_query(
    tables_query,
    connection
)

print(
    "SQL tables:"
)

print(
    tables.to_string(index=False)
)


# --------------------------------------------------
# Verify row counts
# --------------------------------------------------

for table_name in [
    "operations",
    "forecast_backtest",
    "forecast_model_comparison",
]:

    count_query = (
        f"SELECT COUNT(*) AS row_count "
        f"FROM {table_name};"
    )

    row_count = pd.read_sql_query(
        count_query,
        connection
    )

    print(
        f"\n{table_name}:",
        row_count.loc[0, "row_count"],
        "rows"
    )


# --------------------------------------------------
# Close database connection
# --------------------------------------------------

connection.close()

print(
    "\nSQLite database created:",
    database_path
)