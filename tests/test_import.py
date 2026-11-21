import tempfile
from pathlib import Path
import unittest

from sqlalchemy import create_engine, text

from import_data import load_csv


class ImportChecks(unittest.TestCase):
    def test_import_preserves_missing_prices_and_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / "prices.csv"
            csv.write_text("date,open,high,low,close,volume,Name\n2020-01-01,,12,9,11,100,AAA\n", encoding="utf-8")
            engine = create_engine("sqlite:///:memory:")
            load_csv(csv, engine)
            with engine.connect() as connection:
                self.assertIsNone(connection.execute(text("SELECT `open` FROM stock_prices")).scalar())
            with self.assertRaisesRegex(ValueError, "not empty"):
                load_csv(csv, engine)
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM stock_prices")).scalar(), 1)

    def test_invalid_input_does_not_create_table(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / "prices.csv"
            csv.write_text("date,open,high,low,close,volume,Name\n2020-01-01,10,12,9,11,-100,AAA\n", encoding="utf-8")
            engine = create_engine("sqlite:///:memory:")
            with self.assertRaisesRegex(ValueError, "Invalid prices"):
                load_csv(csv, engine)
            with engine.connect() as connection:
                self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE name='stock_prices'")).scalar(), 0)


if __name__ == "__main__":
    unittest.main()
