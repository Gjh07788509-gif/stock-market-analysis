CREATE TABLE IF NOT EXISTS stock_prices (
    `date` DATE NOT NULL,
    `Name` VARCHAR(20) NOT NULL,
    `open` DECIMAL(12,4),
    high DECIMAL(12,4),
    low DECIMAL(12,4),
    `close` DECIMAL(12,4),
    volume BIGINT,
    PRIMARY KEY (`Name`, `date`)
);
