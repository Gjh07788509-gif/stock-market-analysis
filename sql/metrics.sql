WITH history AS (
    SELECT *,
           LAG(`close`) OVER (PARTITION BY `Name` ORDER BY `date`) AS previous_close
    FROM stock_prices_valid
), selected AS (
    SELECT *,
           `close` / NULLIF(previous_close, 0) - 1 AS daily_return,
           ROW_NUMBER() OVER (PARTITION BY `Name` ORDER BY `date`) AS first_row,
           ROW_NUMBER() OVER (PARTITION BY `Name` ORDER BY `date` DESC) AS last_row,
           MAX(`close`) OVER (PARTITION BY `Name` ORDER BY `date`
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_peak
    FROM history
    WHERE `date` BETWEEN :start_date AND :end_date
), summary AS (
    SELECT `Name`, COUNT(*) AS trading_days,
           MAX(CASE WHEN first_row = 1 THEN `close` END) AS first_close,
           MAX(CASE WHEN last_row = 1 THEN `close` END) AS last_close,
           STDDEV_SAMP(CASE WHEN first_row > 1 THEN daily_return END) * SQRT(252) AS annualized_volatility,
           MIN(`close` / NULLIF(running_peak, 0) - 1) AS max_drawdown,
           AVG(volume) AS average_volume
    FROM selected
    GROUP BY `Name`
)
SELECT *, last_close / NULLIF(first_close, 0) - 1 AS period_return
FROM summary
ORDER BY period_return DESC, `Name`;
