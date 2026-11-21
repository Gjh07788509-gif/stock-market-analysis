WITH ranked AS (
    SELECT `Name`, `date`, `close`, EXTRACT(YEAR_MONTH FROM `date`) AS month,
           ROW_NUMBER() OVER (PARTITION BY `Name`, EXTRACT(YEAR_MONTH FROM `date`)
               ORDER BY `date` DESC) AS position
    FROM stock_prices_valid
), month_ends AS (
    SELECT `Name`, month, `close` AS month_end_close,
           LAG(`close`) OVER (PARTITION BY `Name` ORDER BY month) AS previous_month_close
    FROM ranked
    WHERE position = 1
), returns AS (
    SELECT *, month_end_close / NULLIF(previous_month_close, 0) - 1 AS monthly_return
    FROM month_ends
)
SELECT *, DENSE_RANK() OVER (ORDER BY monthly_return DESC) AS return_rank
FROM returns
WHERE month = :month AND monthly_return IS NOT NULL
ORDER BY return_rank, `Name`;
