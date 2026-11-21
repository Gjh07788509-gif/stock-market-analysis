# 股票收益与风险分析 / Stock Market Analysis

面向 SQL 数据分析实习的个人项目：使用 MySQL 8 窗口函数分析股票历史行情，用 Python 导入数据、用 Streamlit 展示收益与风险。项目包含数据质量检查、区间收益排行榜、20/60 日均线、多股票对比、月度收益排名及 CSV 导出。

## 数据与字段

下载 [Kaggle S&P 500 Stock Data](https://www.kaggle.com/datasets/camnugent/sandp500)，解压后使用 `all_stocks_5yr.csv`。数据不随仓库分发，使用时遵循数据集页面的许可要求。本项目不是实时行情服务。

| 字段 | 含义 |
|---|---|
| date | 交易日期 |
| Name | 股票代码 |
| open / high / low / close | 开盘 / 最高 / 最低 / 收盘价 |
| volume | 成交股数 |

一行对应一个股票在一个交易日的行情。具体行数、股票数量、日期范围由应用查询真实导入数据后显示。

## 本地运行（Windows PowerShell）

前提：Python 3.10+、MySQL 8.0+；MySQL 服务已启动。DataGrip 只是客户端，MySQL 才是存储和计算数据的服务器。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

在 DataGrip 查询控制台执行：

```sql
CREATE DATABASE IF NOT EXISTS stock_analysis;
```

设置仅对当前终端生效的连接地址。把用户名、密码替换成你的本机配置；密码包含 `@`、`:`、`/` 等字符时先做 URL 编码。不要把真实连接地址提交到 GitHub。

```powershell
$env:DATABASE_URL = 'mysql+pymysql://YOUR_USER:URL_ENCODED_PASSWORD@localhost:3306/stock_analysis?charset=utf8mb4'
.\.venv\Scripts\python.exe import_data.py 'C:\path\all_stocks_5yr.csv'
.\.venv\Scripts\python.exe -m streamlit run app.py
```

若你已通过 DataGrip 导入 `stock_analysis.stock_prices`，字段与上述一致，可以跳过 Python 导入，直接启动看板。已有表须先检查 `(Name, date)` 是否重复；导入脚本对非空表会停止，避免重复写入或覆盖数据。

## SQL 分析过程

1. `sql/schema.sql`：定义字段类型及股票代码、日期的联合主键。
2. `sql/quality.sql`：统计行数、股票数、日期范围、缺失值与价格逻辑异常。
3. `sql/metrics.sql`：CTE、LAG、ROW_NUMBER 和滚动 MAX 计算收益、波动、回撤。
4. `sql/prices.sql`：计算均线及单只股票的累计价格收益与回撤。
5. `sql/monthly.sql`：提取各月最后一个交易日，以前月末为基准计算月收益，并排名。

带 `:start_date` 等参数的查询由 SQLAlchemy 安全绑定。在 DataGrip 单独练习时，可把参数替换成日期字面量，如 `'2017-01-01'`。

## 指标口径

- 日收益率：当日收盘价 / 上一交易日收盘价 − 1。按股票和日期排序。
- 区间收益：区间最后收盘价 / 第一收盘价 − 1；表示首日收盘买入后的价格变化。
- 年化波动率：区间内日收益率的样本标准差 × √252，排除第一行跨区间的收益；少于两个有效收益时为 NULL。
- 最大回撤：区间内 `收盘价 / 截至当日最高收盘价 − 1` 的最小值，以负数展示。只计算收盘价回撤。
- 均线：最近 20/60 条交易记录的平均收盘价，历史不足时显示空值；筛选区间前的历史也参与预热。
- 月收益：本月最后交易日收盘价 / 数据中前一个有记录月份的月末收盘价 − 1；数据缺月时应先调查，不能直接视作相邻自然月收益。

缺失价格保留为 NULL，不填零。SQL 聚合会忽略部分 NULL，因此缺失值较多的股票需要先排查再解释其指标。交易日期不连续可能来自节假日、停牌、上市时间或数据缺失，不能简单把所有自然日补成交易日。

## 验证

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

检查用一份可手算的小行情验证实际 SQL 的收益、回撤、均线预热及月度排名，使用标准库 SQLite 执行兼容查询。该检查不替代真实 MySQL 上的集成验证。真实数据分析结果及看板截图应在连接本机 MySQL 后生成。

## 局限与研究结论

当前交付为分析工具与可复现查询。未运行完整 Kaggle 数据前，不声称发现市场规律或获得某种策略收益。尚未核实数据复权、分红及历史成分股口径；价格收益不等于投资者含分红总回报，股票池可能存在幸存者偏差。项目没有交易策略、手续费模型或投资建议。

## 简历描述（实际运行并掌握后使用）

**股票历史行情收益与风险分析｜Python、MySQL 8、Streamlit**

- 设计行情数据表及股票代码与日期联合主键，完成 CSV 导入、重复记录校验、缺失值及价格逻辑检查。
- 使用 CTE、LAG、ROW_NUMBER、滚动聚合与 DENSE_RANK，计算区间收益、年化波动率、最大回撤、移动均线和月度收益排名。
- 构建交互分析看板，支持日期筛选、多股票表现对比和指标导出，并明确复权、缺失数据与样本范围对分析结论的限制。

请用实际查询得到的规模补充简历数字；能解释并修改 SQL 后，再把相应能力作为个人技能陈述。

## 发布到 GitHub

项目包含 `publish.ps1`：在安装 GitHub CLI 后运行 `powershell -ExecutionPolicy Bypass -File .\publish.ps1`，按官方网页提示登录 `Gjh07788509-gif`。脚本会创建该账号下的 **私有** `stock-market-analysis` 仓库并推送本地提交。需对该仓库有创建权限，且仓库名尚未占用。需要简历公开链接时，在审阅内容后将仓库改为公开。仓库内附 GitHub Actions，推送后自动运行测试。
