# 股票收益与风险分析 / Stock Market Analysis

用来查看和比较股票历史表现的小工具。行情存入 MySQL，收益、波动率和回撤通过 SQL 计算，Python 负责导入数据和展示图表。

可以按日期筛选数据，比较几只股票的累计收益和回撤，也可以查看 20/60 日均线、月度收益排名，并导出指标表。

## 数据与字段

数据来自 [Kaggle S&P 500 Stock Data](https://www.kaggle.com/datasets/camnugent/sandp500)，使用其中的 `all_stocks_5yr.csv`。需要自行下载并解压，使用许可见数据集页面。页面展示的是历史数据。

| 字段 | 含义 |
|---|---|
| date | 交易日期 |
| Name | 股票代码 |
| open / high / low / close | 开盘 / 最高 / 最低 / 收盘价 |
| volume | 成交股数 |

一行对应一只股票在一个交易日的行情。导入后，页面会显示记录数、股票数量和日期范围。

## 本地运行（Windows PowerShell）

需要 Python 3.10+ 和 MySQL 8.0+。先启动 MySQL，再安装 Python 依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

创建数据库，可在 DataGrip 或 MySQL 命令行执行：

```sql
CREATE DATABASE IF NOT EXISTS stock_analysis;
```

在当前 PowerShell 窗口设置连接地址，再导入 CSV 并启动页面。用户名和密码按本机配置填写，密码中的特殊字符需要做 URL 编码。连接信息不要写入仓库。

```powershell
$env:DATABASE_URL = 'mysql+pymysql://YOUR_USER:URL_ENCODED_PASSWORD@localhost:3306/stock_analysis?charset=utf8mb4'
.\.venv\Scripts\python.exe import_data.py 'C:\path\all_stocks_5yr.csv'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

如果已经通过 DataGrip 导入同名表，字段一致即可跳过导入命令。先检查 `(Name, date)` 是否重复；导入脚本只向空表写入，表里已有数据时会停止。

## 文件说明

1. `sql/schema.sql`：定义字段类型及股票代码、日期的联合主键。
2. `sql/quality.sql`：统计行数、股票数、日期范围、缺失值与价格逻辑异常。
3. `sql/metrics.sql`：CTE、LAG、ROW_NUMBER 和滚动 MAX 计算收益、波动、回撤。
4. `sql/prices.sql`：计算均线及单只股票的累计价格收益与回撤。
5. `sql/monthly.sql`：提取各月最后一个交易日，以前月末为基准计算月收益，并排名。

SQL 中的 `:start_date` 等参数由 SQLAlchemy 传入。在 DataGrip 中直接执行时，可替换成具体日期，如 `'2017-01-01'`。

## 指标口径

- 日收益率：当日收盘价 / 上一交易日收盘价 − 1。按股票和日期排序。
- 区间收益：区间最后收盘价 / 第一收盘价 − 1；表示首日收盘买入后的价格变化。
- 年化波动率：区间内日收益率的样本标准差 × √252，排除第一行跨区间的收益；少于两个有效收益时为 NULL。
- 最大回撤：区间内 `收盘价 / 截至当日最高收盘价 − 1` 的最小值，以负数展示。只计算收盘价回撤。
- 均线：最近 20/60 条交易记录的平均收盘价，历史不足时显示空值；筛选区间前的历史也参与预热。
- 月收益：本月最后交易日收盘价 / 数据中前一个有记录月份的月末收盘价 − 1；数据缺月时应先调查，不能直接视作相邻自然月收益。

缺失价格保留为 NULL，不填零。SQL 聚合会忽略部分 NULL，因此缺失值较多的股票需要先排查再解释其指标。交易日期不连续可能来自节假日、停牌、上市时间或数据缺失，不能简单把所有自然日补成交易日。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

测试使用一组可手算的行情，检查收益、回撤、均线预热、月度排名和导入保护。SQL 测试在 SQLite 上运行，对 MySQL 专有语法做了适配；MySQL 的连接和执行仍需在本地检查。

## 数据说明

这里计算的是价格变化。数据的复权和分红口径还需要核实，因此不能直接当作含分红的投资回报。股票池也可能存在幸存者偏差，比较结果只适用于导入的数据范围。

