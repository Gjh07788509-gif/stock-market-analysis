import argparse
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


def load_csv(csv_path, engine):
    frame = pd.read_csv(csv_path)
    columns = ["date", "Name", "open", "high", "low", "close", "volume"]
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    frame = frame[columns].copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
    if frame[["date", "Name"]].isna().any().any():
        raise ValueError("Missing date or stock symbol")
    if frame["Name"].astype(str).str.strip().eq("").any():
        raise ValueError("Empty stock symbol")
    if frame.duplicated(["Name", "date"]).any():
        raise ValueError("Duplicate symbol/date pairs; inspect the CSV before importing")
    for column in columns[2:]:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    invalid = (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
    invalid |= (frame["volume"] < 0) | (frame["volume"].notna() & (frame["volume"] % 1 != 0))
    invalid |= frame["high"] < frame[["open", "low", "close"]].max(axis=1)
    invalid |= frame["low"] > frame[["open", "high", "close"]].min(axis=1)
    if invalid.any():
        raise ValueError(f"Invalid prices/volume in {int(invalid.sum())} rows")
    schema = (Path(__file__).parent / "sql/schema.sql").read_text(encoding="utf-8")
    with engine.begin() as connection:
        connection.execute(text(schema))
    with engine.begin() as connection:
        if connection.execute(text("SELECT COUNT(*) FROM stock_prices")).scalar():
            raise ValueError("stock_prices is not empty; existing data was preserved")
        frame.to_sql("stock_prices", connection, if_exists="append", index=False, chunksize=2000)
    print(f"Imported {len(frame):,} rows; {frame['Name'].nunique()} symbols")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import Kaggle S&P 500 CSV into an empty MySQL table")
    parser.add_argument("csv", type=Path)
    arguments = parser.parse_args()
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("Set DATABASE_URL first; see README.md")
    load_csv(arguments.csv, create_engine(database_url, pool_pre_ping=True))
