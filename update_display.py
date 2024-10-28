import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import (
    load_hist_data,
    load_bench_cons,
    calculate_percentile,
    plot_line_chart,
    plot_dual_y_line_chart,
    plot_lines_chart,
)

# Load historical data for 沪深300


# Main execution and plotting
if __name__ == "__main__":
    combined_fig = []

    # Plot 指数成交金额
    for bench, name in {
        "000300": "沪深300",
        "000905": "中证500",
        "000852": "中证1000",
    }.items():
        hist_bench_df = pd.read_csv(Path(f"data/hist_of_{bench}.csv"))
        # Calculate and plot 250-day rolling 成交金额 percentile
        VolumeRMB = hist_bench_df["成交金额"].values
        percentile = calculate_percentile(VolumeRMB, 250)
        combined_fig.append(
            plot_dual_y_line_chart(
                x_data=hist_bench_df["日期"].values[249:],
                ys_data=[hist_bench_df["成交金额"].values[249:], percentile],
                names=[f"{name}成交金额", f"{name}成交金额分位数"],
                range_start=75,
            )
        )
        # 计算成分股波动率
        rtn = load_hist_data(indicator="rtn", symols=load_bench_cons(bench))
        vol = rtn.std(axis=1).to_frame()
        percentile = calculate_percentile(vol[0].values, 250)
        combined_fig.append(
            plot_line_chart(
                x_data=vol.index.strftime("%Y-%m-%d")[249:],
                y_data=percentile,
                name=f"{name}成分股波动率分位数",
                range_start=75,
            )
        )
        # 赚钱效应
        bench_rtn = hist_bench_df[["日期", "涨跌幅"]].copy()
        bench_rtn["涨跌幅"] = bench_rtn["涨跌幅"] / 100
        bench_rtn = bench_rtn.set_index("日期").reindex(
            index=rtn.index.strftime("%Y-%m-%d")
        )
        win_ratio = ((rtn.values[-250:, :] - bench_rtn.values[-250:]) > 0).mean(axis=1)
        combined_fig.append(
            plot_line_chart(
                x_data=bench_rtn.index.values[-250:],
                y_data=win_ratio,
                name=f"{name}赚钱效应",
                range_start=75,
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
    cni_399371 = pd.read_csv(Path(r"data/hist_of_399371.csv"))
    cni_399370 = pd.read_csv(Path(r"data/hist_of_399370.csv"))
    cni_399371["rtn"] = cni_399371["收盘价"].pct_change()
    cni_399370["rtn"] = cni_399370["收盘价"].pct_change()
    combined_fig.append(
        plot_line_chart(
            x_data=cni_399371["日期"].values[-100:],
            y_data=cni_399371["rtn"].values[-100:] - cni_399370["rtn"].values[-100:],
            name="价值VS成长相对强弱",
            range_start=75,
        )
    )

    # Plot IC and IM data with dual Y-axis
    IC_data = pd.read_csv(Path(r"data/IC_data.csv"))
    IM_data = pd.read_csv(Path(r"data/IM_data.csv"))

    combined_fig.append(
        plot_lines_chart(
            x_data=IC_data["日期"],
            ys_data=[IC_data["年化基差(%)"], IM_data["年化基差(%)"]],
            names=["IC年化基差(%)", "IM年化基差(%)"],
            range_start=75,
        )
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
                #timestamp {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    font-size: 12px;
                    color: #999;
                }}
            </style>
        </head>
        <body>
            <div id="timestamp">Last Updated: {datetime.now(ZoneInfo('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")}</div>
            {"".join([chart.render_embed() for chart in combined_fig])}
        </body>
    </html>"""
    # Write the combined figure to an HTML file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
