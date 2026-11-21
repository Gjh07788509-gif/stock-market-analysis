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
except Exception:
    st.error("数据库连接或查询失败。请检查 MySQL 服务、连接配置、版本及 stock_prices 表。")
    st.stop()
if quality.iloc[0]["row_count"] == 0:
    st.warning("stock_prices 表为空，请先导入 CSV。")
    st.stop()

overview = quality.iloc[0]
st.write(f"数据范围：{overview['first_date']} 至 {overview['last_date']}")
st.dataframe(quality, hide_index=True)
if overview["duplicate_pairs"] > 0 or overview["invalid_rows"] > 0:
    st.error("存在重复股票日期或异常行情，请先检查原始数据再计算指标。")
    st.stop()
if overview["incomplete_rows"] > 0:
    st.warning("存在缺失字段，收益与风险指标可能不完整；请结合数据质量报告解释结果。")
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
