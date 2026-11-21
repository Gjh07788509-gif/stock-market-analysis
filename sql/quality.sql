SELECT (SELECT COUNT(*) FROM (
           SELECT `Name`, `date` FROM stock_prices
           GROUP BY `Name`, `date` HAVING COUNT(*) > 1
       ) AS duplicates) AS duplicate_pairs,
       COUNT(*) AS row_count,
       COUNT(DISTINCT `Name`) AS stock_count,
       MIN(`date`) AS first_date,
       MAX(`date`) AS last_date,
       SUM(CASE WHEN `open` IS NULL OR high IS NULL OR low IS NULL
                     OR `close` IS NULL OR volume IS NULL THEN 1 ELSE 0 END) AS incomplete_rows,
       SUM(CASE WHEN `open` <= 0 OR high <= 0 OR low <= 0 OR `close` <= 0
                     OR volume < 0 OR high < low OR high < `open`
                     OR high < `close` OR low > `open` OR low > `close`
                THEN 1 ELSE 0 END) AS invalid_rows
FROM stock_prices;
