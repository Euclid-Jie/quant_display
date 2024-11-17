import pandas as pd
import numpy as np
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
    load_speed_of_indus,
    load_speed_of_barra,
)
from window import rolling_mean
from barra_data import BarraData
from typing import List


class Specify_dict(dict):
    def update(self, data: dict):
        for key, value in data.items():
            eixt_value: List = self.get(key)
            eixt_value.append(value)
            self[key] = eixt_value


display_dict = {}

# Main execution and plotting
if __name__ == "__main__":
    combined_fig = Specify_dict(
        {
            "base": [],
            "中证全指": [],
            "沪深300": [],
            "中证500": [],
            "中证1000": [],
            "中证2000": [],
        }
    )
    # barra 风格因子
    barra_data = BarraData(Path("data"))
    cne5 = barra_data.load_data("cne5").iloc[-20:]
    cne5["日期"] = np.datetime_as_string(cne5["日期"], unit="D")
    cne5.set_index("日期", inplace=True)
    cne5.iloc[0, :] = 0
    cne5_nav = (1 + cne5).cumprod()
    combined_fig.update(
        {
            "base": plot_lines_chart(
                x_data=cne5_nav.index,
                ys_data=[cne5_nav[col].values.round(3) for col in cne5_nav.columns],
                names=[col for col in cne5_nav.columns],
                lower_bound=np.round(min(cne5_nav.min().values) - 0.02, 2),
            )
        }
    )

    # Plot 指数成交金额
    all_volumeRMB = []
    for bench, name in {
        "000985": "中证全指",
        "000300": "沪深300",
        "000905": "中证500",
        "000852": "中证1000",
        "932000": "中证2000",
    }.items():
        volumeRMB = pd.read_csv(Path(f"data/hist_of_{bench}.csv"))["成交金额"].values
        weekly_mean_volumeRMB = rolling_mean(volumeRMB, 5).round(2)[249:]
        all_volumeRMB.append(weekly_mean_volumeRMB)
        display_dict.update(
            {
                f"{name}成交金额MA5": [
                    weekly_mean_volumeRMB[-1],
                    weekly_mean_volumeRMB[-6],
                ]
            }
        )

    combined_fig.update(
        {
            "base": plot_lines_chart(
                x_data=pd.read_csv(Path(f"data/hist_of_{bench}.csv"))["日期"].values[
                    249:
                ],
                ys_data=all_volumeRMB,
                names=[
                    f"{name}成交金额MA5"
                    for name in [
                        "中证全指",
                        "沪深300",
                        "中证500",
                        "中证1000",
                        "中证2000",
                    ]
                ],
                range_start=75,
            )
        }
    )

    # Plot 指数成交金额
    for bench, name in {
        "000985": "中证全指",
        "000300": "沪深300",
        "000905": "中证500",
        "000852": "中证1000",
        "932000": "中证2000",
    }.items():
        hist_bench_df = pd.read_csv(Path(f"data/hist_of_{bench}.csv"))
        # Calculate and plot 250-day rolling 成交金额 percentile
        VolumeRMB = hist_bench_df["成交金额"].values
        percentile = calculate_percentile(VolumeRMB, 250)
        combined_fig.update(
            {
                name: plot_dual_y_line_chart(
                    x_data=hist_bench_df["日期"].values[249:],
                    ys_data=[hist_bench_df["成交金额"].values[249:], percentile],
                    names=[f"{name}成交金额", f"{name}成交金额分位数"],
                    range_start=75,
                )
            }
        )
        # 计算成分股波动率
        rtn = load_hist_data(
            indicator="rtn",
            symols=load_bench_cons(bench),
            end_date=np.datetime64("today") - np.timedelta64(1, "D"),
        )
        vol = rtn.std(axis=1).to_frame()
        percentile = calculate_percentile(vol[0].values, 250)
        weekly_mean_percentile = rolling_mean(percentile, 5).round(3)
        display_dict.update(
            {
                f"{name}波动率分位数MA5": [
                    weekly_mean_percentile[-1],
                    weekly_mean_percentile[-6],
                ]
            }
        )
        combined_fig.update(
            {
                name: plot_lines_chart(
                    x_data=vol.index.strftime("%Y-%m-%d")[249:],
                    ys_data=[
                        percentile,
                        weekly_mean_percentile.round(3),
                    ],
                    names=[
                        f"{name}成分股波动率分位数",
                        f"{name}成分股波动率分位数MA5",
                    ],
                    range_start=75,
                )
            }
        )
        # 赚钱效应
        # NOTE: bench rtn 只会有前一天的数据, 而rtn中会有当天的数据, 故需要剔除最后一天的数据
        bench_rtn = hist_bench_df[["日期", "涨跌幅"]].copy()
        bench_rtn["涨跌幅"] = bench_rtn["涨跌幅"] / 100
        bench_rtn = bench_rtn.set_index("日期").reindex(
            index=rtn.index.strftime("%Y-%m-%d")
        )
        win_ratio = ((rtn.values[-250:, :] - bench_rtn.values[-250:]) > 0).mean(axis=1)
        combined_fig.update(
            {
                name: plot_lines_chart(
                    x_data=bench_rtn.index.values[-250:],
                    ys_data=[win_ratio.round(3), rolling_mean(win_ratio, 5).round(3)],
                    names=[f"{name}赚钱效应", f"{name}赚钱效应MA5"],
                    range_start=75,
                )
            }
        )

    # Plot 大小盘相对强弱
    big_df = pd.read_csv(Path(r"data/801811.SI.csv"))
    small_df = pd.read_csv(Path(r"data/801813.SI.csv"))
    big_df["rtn"] = big_df["PCT_CHG"].values / 100
    small_df["rtn"] = small_df["PCT_CHG"].values / 100
    big_vs_small = big_df["rtn"] - small_df["rtn"]
    combined_fig.update(
        {
            "base": plot_line_chart(
                x_data=big_df["日期"].values[-100:],
                y_data=big_vs_small.values[-100:].round(3),
                name="大小盘相对强弱",
                range_start=75,
            )
        }
    )
    display_dict.update(
        {
            "大小盘相对强弱": [
                big_vs_small.values[-1],
                big_vs_small.values[-6],
            ]
        }
    )

    # Plot 价值VS成长相对强弱
    cni_399371 = pd.read_csv(Path(r"data/hist_of_399371.csv"))
    cni_399370 = pd.read_csv(Path(r"data/hist_of_399370.csv"))
    cni_399371["rtn"] = cni_399371["收盘价"].pct_change()
    cni_399370["rtn"] = cni_399370["收盘价"].pct_change()
    value_vs_growth = cni_399371["rtn"] - cni_399370["rtn"]
    combined_fig.update(
        {
            "base": plot_line_chart(
                x_data=cni_399371["日期"].values[-100:],
                y_data=value_vs_growth.values[-100:].round(3),
                name="价值VS成长相对强弱",
                range_start=75,
            )
        }
    )
    display_dict.update(
        {
            "价值VS成长相对强弱": [
                value_vs_growth.values[-1],
                value_vs_growth.values[-6],
            ]
        }
    )

    # 行业轮动
    speed_of_idus_monthly, speed_of_idus_weekly = load_speed_of_indus(Path(r"data/sw1"))
    combined_fig.update(
        {
            "base": plot_lines_chart(
                x_data=speed_of_idus_monthly.index[-100:],
                ys_data=[
                    speed_of_idus_monthly.iloc[-100:, 0].values,
                    speed_of_idus_weekly.iloc[-100:, 0].values,
                ],
                names=["行业轮动速度(月)", "行业轮动速度(周)"],
                range_start=75,
                lower_bound=min(
                    min(speed_of_idus_monthly.iloc[-100:, 0].values),
                    min(speed_of_idus_weekly.iloc[-100:, 0].values),
                )
                - 0.02,
            )
        }
    )
    display_dict.update(
        {
            "行业轮动速度(月)": [
                speed_of_idus_monthly.iloc[-1, 0],
                speed_of_idus_monthly.iloc[-6, 0],
            ],
            "行业轮动速度(周)": [
                speed_of_idus_weekly.iloc[-1, 0],
                speed_of_idus_weekly.iloc[-6, 0],
            ],
        }
    )
    # barra 轮动速度
    speed_of_barra_monthly, speed_of_barra_weekly = load_speed_of_barra()
    combined_fig.update(
        {
            "base": plot_lines_chart(
                x_data=np.datetime_as_string(
                    speed_of_barra_monthly.index[-100:], unit="D"
                ),
                ys_data=[
                    speed_of_barra_monthly.iloc[-100:, 0].values,
                    speed_of_barra_weekly.iloc[-100:, 0].values,
                ],
                names=["Barra轮动速度(月)", "Barra轮动速度(周)"],
                range_start=75,
                lower_bound=min(
                    min(speed_of_barra_monthly.iloc[-100:, 0].values),
                    min(speed_of_barra_weekly.iloc[-100:, 0].values),
                )
                - 0.02,
            )
        }
    )
    display_dict.update(
        {
            "Barra轮动速度(月)": [
                speed_of_barra_monthly.iloc[-1, 0],
                speed_of_barra_monthly.iloc[-6, 0],
            ],
            "Barra轮动速度(周)": [
                speed_of_barra_weekly.iloc[-1, 0],
                speed_of_barra_weekly.iloc[-6, 0],
            ],
        }
    )

    # Plot IC and IM data with dual Y-axis
    IC_data = pd.read_csv(Path(r"data/IC_data.csv"))
    IM_data = pd.read_csv(Path(r"data/IM_data.csv"))

    combined_fig.update(
        {
            "base": plot_lines_chart(
                x_data=IC_data["日期"],
                ys_data=[IC_data["年化基差(%)"], IM_data["年化基差(%)"]],
                names=["IC年化基差(%)", "IM年化基差(%)"],
                range_start=75,
            )
        }
    )
    display_dict.update(
        {
            "IC年化基差(%)": [
                IC_data["年化基差(%)"].values[-1],
                IC_data["年化基差(%)"].values[-6],
            ],
            "IM年化基差(%)": [
                IM_data["年化基差(%)"].values[-1],
                IM_data["年化基差(%)"].values[-6],
            ],
        }
    )
    display_df = pd.DataFrame(display_dict, index=["当期", "上期(T-5)"]).T
    display_df["变化"] = display_df["当期"] - display_df["上期(T-5)"]
    display_df["变化%"] = display_df["变化"] / display_df["上期(T-5)"]
    display_df["变化%"] = display_df["变化%"].apply(lambda x: f"{x:.2%}")
    # 如果 "当期" 或者 "上期(T-5)" 为负数, 则 "变化%" 为 NULL
    display_df.loc[
        (display_df["当期"] < 0) | (display_df["上期(T-5)"] < 0), "变化%"
    ] = np.nan
    # Plot the combined figure
    tmp_html = ""
    for i, raws in combined_fig.items():
        tmp_html += f"""
            <details open>
                <summary style="background-color: #f0f0f0; padding: 20px; border-radius: 10px; cursor: pointer;">{i}</summary>
                <div style="margin-top: 10px;">
                    <div>Last Updated: {datetime.now(ZoneInfo('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")}</div>
                    {display_df.T.to_html(render_links=True) if i == "base" else ""}
                    {cne5.iloc[-5:].to_html() if i == "base" else ""}
                    {"".join([chart.render_embed() for chart in raws])}
                </div>
            </details>
        """

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
            {tmp_html}
        </body>
    </html>"""
    # Write the combined figure to an HTML file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
