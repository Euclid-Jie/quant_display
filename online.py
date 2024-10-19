import numpy as np
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from pyecharts.charts import Line, Grid
from pyecharts import options as opts
from pyecharts.globals import ThemeType
from unitls import load_bais


# Function to generate a line chart
def plot_line_chart(x_data, y_data, title, name):
    line = (
        Line(
            init_opts={
                "width": "1560px",
                "height": "600px",
                "is_horizontal_center": True,
            }
        )
        .add_xaxis(list(x_data))
        .add_yaxis(name, list(y_data), is_symbol_show=False)
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(type_="category"),
            yaxis_opts=opts.AxisOpts(type_="value"),
            legend_opts=opts.LegendOpts(
                textstyle_opts=opts.TextStyleOpts(font_weight="bold", font_size=20)
            ),
            datazoom_opts=[
                opts.DataZoomOpts(range_start=0, range_end=100, orient="horizontal")
            ],
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
        .set_series_opts(
            linestyle_opts=opts.LineStyleOpts(width=3),
        )
    )
    return line


# Function to calculate rolling percentile
def calculate_percentile(data, window_size):
    data_windows = np.lib.stride_tricks.as_strided(
        data, (len(data) - window_size + 1, window_size), (data.itemsize, data.itemsize)
    )
    percentile = (
        np.sum(data_windows <= data_windows[:, -1][:, None], axis=1)
        / data_windows.shape[1]
    )
    return percentile


# Function to add dual Y-axis chart
def plot_dual_axis_chart(data, title, key):
    line1 = (
        Line()
        .add_xaxis(list(data["日期"][-100:]))
        .add_yaxis(
            f"{key}年化基差(%)",
            list(data["年化基差(%)"][-100:]),
            yaxis_index=0,
            is_smooth=True,
        )
        .extend_axis(
            yaxis=opts.AxisOpts(name="期货&现货价格", type_="value", position="right")
        )
    )

    line2 = (
        Line()
        .add_xaxis(list(data["日期"][-100:]))
        .add_yaxis(
            "现货价格", list(data["现货价格"][-100:]), yaxis_index=1, is_smooth=True
        )
        .add_yaxis(
            "期货价格", list(data["期货价格"][-100:]), yaxis_index=1, is_smooth=True
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center"),
            yaxis_opts=opts.AxisOpts(
                name="年化基差", type_="value", position="left", min_=-20, max_=20
            ),
            xaxis_opts=opts.AxisOpts(type_="category"),
        )
    )

    grid = Grid()
    grid.add(line1, grid_opts=opts.GridOpts(pos_left="5%"))
    grid.add(line2, grid_opts=opts.GridOpts(pos_right="5%"))
    return grid


# Load historical data for 沪深300
def load_bench300_hist():
    hist_df = ak.stock_zh_index_hist_csindex(
        symbol="000300",
        start_date=(datetime.now() - timedelta(days=2 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    # hist_df["日期"] = pd.to_datetime(hist_df["日期"])
    return hist_df


# Main execution and plotting
if __name__ == "__main__":
    combined_fig = []

    # Plot 沪深300指数成交金额
    hist_of_bench300_df = load_bench300_hist()
    combined_fig.append(
        plot_line_chart(
            hist_of_bench300_df["日期"],
            hist_of_bench300_df["成交金额"],
            "沪深300指数成交金额",
            "成交金额",
        )
    )

    # Calculate and plot 250-day rolling 成交金额 percentile
    VolumeRMB = hist_of_bench300_df["成交金额"].values
    percentile = calculate_percentile(VolumeRMB, 250)
    combined_fig.append(
        plot_line_chart(
            hist_of_bench300_df["日期"][249:],
            percentile,
            "沪深300指数成交金额分位数",
            "成交金额分位数",
        )
    )

    # # Plot 大小盘相对强弱
    # big_df = ak.index_hist_sw(symbol="801811", period="day")
    # small_df = ak.index_hist_sw(symbol="801813", period="day")
    # big_df["rtn"] = big_df["收盘"].pct_change()
    # small_df["rtn"] = small_df["收盘"].pct_change()
    # big_de_small = big_df["rtn"] - small_df["rtn"]
    # combined_fig.append(
    #     plot_line_chart(
    #         big_df["日期"].values[-100:],
    #         big_de_small.values[-100:],
    #         "大小盘相对强弱",
    #         "大小盘相对强弱",
    #     )
    # )

    # Plot 价值VS成长相对强弱
    cni_399371 = ak.index_hist_cni(
        symbol="399371",
        start_date=(datetime.now() - timedelta(days=2 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    cni_399370 = ak.index_hist_cni(
        symbol="399370",
        start_date=(datetime.now() - timedelta(days=2 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    cni_399371["rtn"] = cni_399371["收盘价"].pct_change()
    cni_399370["rtn"] = cni_399370["收盘价"].pct_change()
    combined_fig.append(
        plot_line_chart(
            cni_399371["日期"].values[-100:],
            cni_399371["rtn"].values[-100:] - cni_399370["rtn"].values[-100:],
            "价值VS成长相对强弱",
            "价值VS成长相对强弱",
        )
    )

    # Plot IC and IM data with dual Y-axis
    IC_data = load_bais("IC")
    IM_data = load_bais("IM")

    for key, data in {"IC年化基差(%)": IC_data, "IM年化基差(%)": IM_data}.items():
        combined_fig.append(
            plot_line_chart(data["日期"], data["年化基差(%)"], key, key)
        )

    html = f"""<html>
        <head>
            <meta charset="UTF-8">
            <title>Value over Time</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                table {{
                    margin: auto;
                    margin-bottom: 20px;
                    border-collapse: collapse;
                    width: 80%;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center; 
                }}
                th {{
                    background-color: #f59e00;
                    color: white;
                }}
            </style>
        </head>
        <body>
            {"".join([chart.render_embed() for chart in combined_fig])}
        </body>
    </html>"""
    # Write the combined figure to an HTML file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
