import numpy as np
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.offline as pyo
from numpy.lib.stride_tricks import as_strided
from plotly.subplots import make_subplots
from unitls import load_bais

# Function to generate a line chart
def plot_line_chart(x_data, y_data, title, name):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode="lines",
            name=name
        )
    )
    fig.update_layout(title_text=title, title_x=0.5)
    return fig

# Function to calculate rolling percentile
def calculate_percentile(data, window_size):
    data_windows = as_strided(data, (len(data) - window_size + 1, window_size), (data.itemsize, data.itemsize))
    percentile = np.sum(data_windows <= data_windows[:, -1][:, None], axis=1) / data_windows.shape[1]
    return percentile

# Function to add subplot with dual Y-axis
def plot_dual_axis_chart(data, title, key):
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Left Y-axis: Annualized basis
    fig.add_trace(
        go.Scatter(
            x=data["日期"][-100:],
            y=data["年化基差(%)"][-100:],
            mode="lines",
            name=f"{key}年化基差(%)",
        ), secondary_y=False,
    )
    
    # Right Y-axis: Spot and Futures Prices
    fig.add_trace(
        go.Scatter(
            x=data["日期"][-100:],
            y=data["现货价格"][-100:],
            mode="lines",
            name="现货价格",
        ), secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=data["日期"][-100:],
            y=data["期货价格"][-100:],
            mode="lines",
            name="期货价格",
        ), secondary_y=True,
    )

    # Update axes titles
    fig.update_xaxes(title_text="日期")
    fig.update_yaxes(title_text="年化基差", secondary_y=False)
    fig.update_yaxes(title_text="期货&现货价格", secondary_y=True)

    # Set Y-axis ranges
    fig.update_yaxes(range=[-20, 20], secondary_y=False)
    fig.update_layout(title_text=title, title_x=0.5)
    return fig

# Load historical data for 沪深300
def load_bench300_hist():
    hist_df = ak.stock_zh_index_hist_csindex(
        symbol="000300",
        start_date=(datetime.now() - timedelta(days=2 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    hist_df["日期"] = pd.to_datetime(hist_df["日期"])
    return hist_df

# Main execution and plotting
if __name__ == "__main__":
    combined_fig = ""

    # Plot 沪深300指数成交金额
    hist_of_bench300_df = load_bench300_hist()
    combined_fig += pyo.plot(plot_line_chart(hist_of_bench300_df["日期"], hist_of_bench300_df["成交金额"], "沪深300指数成交金额", "成交金额"), output_type="div")

    # Calculate and plot 250-day rolling 成交金额 percentile
    VolumeRMB = hist_of_bench300_df["成交金额"].values
    percentile = calculate_percentile(VolumeRMB, 250)
    combined_fig += pyo.plot(plot_line_chart(hist_of_bench300_df["日期"][249:], percentile, "沪深300指数成交金额分位数", "成交金额分位数"), output_type="div")

    # Plot 大小盘相对强弱
    big_df = ak.index_hist_sw(symbol="801811", period="day")
    small_df = ak.index_hist_sw(symbol="801813", period="day")
    big_df["rtn"] = big_df["收盘"].pct_change()
    small_df["rtn"] = small_df["收盘"].pct_change()
    big_de_small = big_df["rtn"] - small_df["rtn"]
    combined_fig += pyo.plot(plot_line_chart(big_df["日期"].values[-100:], big_de_small.values[-100:], "大小盘相对强弱", "大小盘相对强弱"), output_type="div")

    # Plot 价值VS成长相对强弱
    cni_399371 = ak.index_hist_cni(symbol="399371", start_date="20231014", end_date="20241014")
    cni_399370 = ak.index_hist_cni(symbol="399370", start_date="20231014", end_date="20241014")
    cni_399371["rtn"] = cni_399371["收盘价"].pct_change()
    cni_399370["rtn"] = cni_399370["收盘价"].pct_change()
    combined_fig += pyo.plot(plot_line_chart(big_df["日期"].values[-100:], cni_399371["rtn"].values[-100:] - cni_399370["rtn"].values[-100:], "价值VS成长相对强弱", "价值VS成长相对强弱"), output_type="div")

    # Plot IC and IM data with dual Y-axis
    IC_data = load_bais("IC")
    IM_data = load_bais("IM")
    
    for key, data in {"IC": IC_data, "IM": IM_data}.items():
        combined_fig += pyo.plot(plot_dual_axis_chart(data, f"{key}基差与现货价格", key), output_type="div")

    # Write the combined figure to an HTML file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(combined_fig)
