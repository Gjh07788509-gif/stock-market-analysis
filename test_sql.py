import math
from pathlib import Path
import sqlite3
import statistics
import unittest


SQL = Path(__file__).resolve().parents[1] / "sql"


class StandardDeviation:
    def __init__(self):
        self.values = []

    def step(self, value):
        if value is not None:
            self.values.append(value)

    def finalize(self):
        return statistics.stdev(self.values) if len(self.values) > 1 else None


class AnalysisChecks(unittest.TestCase):
    def setUp(self):
        self.database = sqlite3.connect(":memory:")
        self.database.row_factory = sqlite3.Row
        self.database.create_aggregate("STDDEV_SAMP", 1, StandardDeviation)
        self.database.create_function("SQRT", 1, math.sqrt)
        self.database.executescript((SQL / "schema.sql").read_text().replace("DECIMAL(12,4)", "REAL"))
        rows = [
            ("2020-01-30", "AAA", 100, 100, 100, 100, 1000),
            ("2020-01-31", "AAA", 120, 120, 120, 120, 1200),
            ("2020-02-03", "AAA", 90, 90, 90, 90, 1500),
            ("2020-02-28", "AAA", 108, 108, 108, 108, 1300),
            ("2020-01-31", "BBB", 50, 50, 50, 50, 500),
            ("2020-02-28", "BBB", 60, 60, 60, 60, 600),
        ]
        self.database.executemany("INSERT INTO stock_prices VALUES (?,?,?,?,?,?,?)", rows)
        self.database.executescript((SQL / "clean.sql").read_text().replace("CREATE OR REPLACE VIEW", "CREATE VIEW"))

    def tearDown(self):
        self.database.close()

    def query(self, filename, **parameters):
        sql = (SQL / filename).read_text()
        sql = sql.replace("EXTRACT(YEAR_MONTH FROM `date`)", "CAST(strftime('%Y%m', `date`) AS INTEGER)")
        return self.database.execute(sql, parameters).fetchall()

    def test_metrics_and_quality(self):
        results = self.query("metrics.sql", start_date="2020-01-30", end_date="2020-02-28")
        self.assertEqual(results[0]["Name"], "BBB")
        stock = results[1]
        self.assertAlmostEqual(stock["period_return"], 0.08)
        self.assertAlmostEqual(stock["max_drawdown"], -0.25)
        self.assertAlmostEqual(stock["annualized_volatility"], statistics.stdev([0.2, -0.25, 0.2]) * math.sqrt(252))
        self.assertEqual(self.query("quality.sql")[0]["invalid_rows"], 0)

    def test_clean_view_filters_invalid_and_missing_without_changing_source(self):
        self.database.executemany("INSERT INTO stock_prices VALUES (?,?,?,?,?,?,?)", [
            ("2020-03-01", "AAA", 100, 90, 80, 100, 100),
            ("2020-03-02", "AAA", None, 100, 80, 90, 100),
        ])
        self.assertEqual(self.database.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0], 8)
        self.assertEqual(self.database.execute("SELECT COUNT(*) FROM stock_prices_valid").fetchone()[0], 6)
        results = self.query("metrics.sql", start_date="2020-01-30", end_date="2020-03-02")
        self.assertAlmostEqual(results[1]["period_return"], 0.08)

    def test_date_boundaries_and_months(self):
        prices = self.query("prices.sql", symbol="AAA", start_date="2020-02-03", end_date="2020-02-28")
        self.assertAlmostEqual(prices[0]["drawdown"], 0)
        self.assertAlmostEqual(prices[-1]["cumulative_return"], 0.2)
        self.assertIsNone(prices[-1]["ma20"])
        monthly = self.query("monthly.sql", month=202002)
        self.assertEqual(monthly[0]["Name"], "BBB")
        self.assertAlmostEqual(monthly[1]["monthly_return"], -0.1)
        self.assertEqual(monthly[1]["return_rank"], 2)

    def test_moving_average_uses_earlier_history(self):
        from datetime import date, timedelta

        rows = [(str(date(2019, 1, 1) + timedelta(days=offset)), "CCC", value, value, value, value, 100)
                for offset, value in enumerate(range(1, 61))]
        self.database.executemany("INSERT INTO stock_prices VALUES (?,?,?,?,?,?,?)", rows)
        prices = self.query("prices.sql", symbol="CCC", start_date="2019-03-01", end_date="2019-03-01")
        self.assertAlmostEqual(prices[0]["ma20"], 50.5)
        self.assertAlmostEqual(prices[0]["ma60"], 30.5)


if __name__ == "__main__":
    unittest.main()
