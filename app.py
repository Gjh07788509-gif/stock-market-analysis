import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text


st.set_page_config(page_title="股票收益与风险分析", layout="wide")
st.title("股票收益与风险分析")
st.caption("MySQL 8 · Python · Kaggle 历史日行情")
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    st.info("请先按 README 设置 DATABASE_URL，再启动应用。")
    st.stop()


@st.cache_resource
def connect(url):
    return create_engine(url, pool_pre_ping=True)


engine = connect(database_url)


def query(filename, parameters=None):
    statement = (Path(__file__).parent / "sql" / filename).read_text(encoding="utf-8")
    with engine.connect() as connection:
        return pd.read_sql(text(statement), connection, params=parameters or {})


try:
    quality = query("quality.sql")
except Exception as error:
    st.error("数据库连接或查询失败。请检查 MySQL 服务、连接配置、版本及 stock_prices 表。")
    original = getattr(error, "orig", error)
    arguments = getattr(original, "args", ())
    code = arguments[0] if arguments and isinstance(arguments[0], int) else None
    hints = {
        1045: "账号或密码不正确，或该用户没有连接权限。请核对 DataGrip 的连接设置。",
        1044: "当前用户没有访问 stock_analysis 数据库的权限。",
        1049: "连接地址中的数据库不存在。请核对数据库名称。",
        1146: "找不到 stock_prices 表。请确认已导入，并核对表名。",
        1054: "数据表字段与项目不一致。需要 date、Name、open、high、low、close、volume。",
        1064: "SQL 语法错误。请检查 MySQL 版本及 sql/quality.sql。",
        2003: "无法连接 MySQL。请检查服务是否启动，以及主机、端口是否正确。",
    }
    st.info(hints.get(code, "请在 DataGrip 中执行 sql/quality.sql，查看具体查询错误。"))
    st.caption(f"错误类型：{type(original).__name__}；错误码：{code if code is not None else '无'}")
    st.stop()
if quality.iloc[0]["row_count"] == 0:
    st.warning("stock_prices 表为空，请先导入 CSV。")
    st.stop()

overview = quality.iloc[0]
st.write(f"数据范围：{overview['first_date']} 至 {overview['last_date']}")
st.dataframe(quality, hide_index=True)
if overview["duplicate_pairs"] > 0:
    st.error("存在重复股票日期，请先检查原始数据。")
    st.stop()
try:
    with engine.connect() as connection:
        valid_count = connection.execute(text("SELECT COUNT(*) FROM stock_prices_valid")).scalar_one()
except Exception:
    st.error("请在 DataGrip 中选择 stock_analysis，执行 sql/clean.sql 创建清洗视图，再刷新页面。")
    st.stop()
st.caption(f"用于分析：{valid_count:,} 条；排除缺失或异常记录：{int(overview['row_count']) - valid_count:,} 条。原表保留不变。")
if valid_count == 0:
    st.warning("没有可用于分析的完整有效行情。")
    st.stop()
st.caption("收益按相邻有效记录计算；若中间记录被排除，收益可能跨越多个交易日，年化波动率仅作近似参考。")
start_date = st.sidebar.date_input("开始日期", pd.Timestamp(overview["first_date"]).date())
end_date = st.sidebar.date_input("结束日期", pd.Timestamp(overview["last_date"]).date())
if start_date > end_date:
    st.warning("开始日期不能晚于结束日期。")
    st.stop()
parameters = {"start_date": start_date, "end_date": end_date}
metrics = query("metrics.sql", parameters)
if metrics.empty:
    st.info("所选日期没有数据。")
    st.stop()

st.subheader("区间收益与风险排行榜")
st.caption("收益为区间首末收盘价变化；回撤为区间内收盘价回撤；波动率采用 252 个交易日年化。")
st.dataframe(metrics, hide_index=True)
symbols = metrics["Name"].sort_values().tolist()
selected = st.sidebar.multiselect("比较股票（最多 5 只）", symbols, default=symbols[:1], max_selections=5)
series = [query("prices.sql", {**parameters, "symbol": symbol}) for symbol in selected]
if series:
    prices = pd.concat(series, ignore_index=True)
    st.plotly_chart(px.line(prices, x="date", y="cumulative_return", color="Name", title="累计价格收益（各自从区间首日归零）"), use_container_width=True)
    st.plotly_chart(px.line(prices, x="date", y="drawdown", color="Name", title="区间内回撤"), use_container_width=True)
    single = prices[prices["Name"] == selected[0]]
    st.plotly_chart(px.line(single, x="date", y=["close", "ma20", "ma60"], title=f"{selected[0]} 收盘价与均线"), use_container_width=True)

month = st.number_input("月度排名：输入年月，如 201701", min_value=190001, max_value=210012, value=int(pd.Timestamp(end_date).strftime("%Y%m")), step=1)
if 1 <= int(month) % 100 <= 12:
    monthly = query("monthly.sql", {"month": int(month)})
    st.dataframe(monthly, hide_index=True)
else:
    st.warning("月份须为 01—12。")
st.download_button("下载区间指标 CSV", metrics.to_csv(index=False).encode("utf-8-sig"), "stock_metrics.csv", "text/csv")
st.caption("历史研究用途。未确认复权口径前，价格收益不应解释为包含分红的实际投资回报；股票池可能存在幸存者偏差。")
