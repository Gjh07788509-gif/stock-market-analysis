WITH history AS (
    SELECT `date`, `Name`, `close`, volume,
           AVG(`close`) OVER (PARTITION BY `Name` ORDER BY `date`
               ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS ma20_value,
           AVG(`close`) OVER (PARTITION BY `Name` ORDER BY `date`
               ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS ma60_value,
           COUNT(`close`) OVER (PARTITION BY `Name` ORDER BY `date`
               ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS observations20,
           COUNT(`close`) OVER (PARTITION BY `Name` ORDER BY `date`
               ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS observations60
    FROM stock_prices_valid
    WHERE `Name` = :symbol
)
SELECT `date`, `Name`, `close`, volume,
       CASE WHEN observations20 = 20 THEN ma20_value END AS ma20,
       CASE WHEN observations60 = 60 THEN ma60_value END AS ma60,
       `close` / NULLIF(FIRST_VALUE(`close`) OVER (ORDER BY `date`), 0) - 1 AS cumulative_return,
       `close` / NULLIF(MAX(`close`) OVER (ORDER BY `date`
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) - 1 AS drawdown
FROM history
WHERE `date` BETWEEN :start_date AND :end_date
ORDER BY `date`;
