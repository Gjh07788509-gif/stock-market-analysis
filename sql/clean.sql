CREATE OR REPLACE VIEW stock_prices_valid AS
SELECT *
FROM stock_prices
WHERE `date` IS NOT NULL
  AND `Name` IS NOT NULL
  AND TRIM(`Name`) <> ''
  AND `open` IS NOT NULL
  AND high IS NOT NULL
  AND low IS NOT NULL
  AND `close` IS NOT NULL
  AND volume IS NOT NULL
  AND `open` > 0
  AND high > 0
  AND low > 0
  AND `close` > 0
  AND volume >= 0
  AND high >= low
  AND high >= `open`
  AND high >= `close`
  AND low <= `open`
  AND low <= `close`;
