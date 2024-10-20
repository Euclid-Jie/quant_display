from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
from pathlib import Path
from H5DataBase import H5DataBase
from datetime import datetime
from typing import Literal, List
import requests
import re
import urllib.parse
import json
import uuid


__all__ = [
    "load_bais",
    "now_time",
    "pivoted_df_insert_rows",
    "load_hist_data",
    "load_bench_cons",
    "calculate_percentile",
]


def now_time():
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


# Function to calculate rolling percentile
def calculate_percentile(data: np.ndarray, window_size: int) -> np.ndarray:
    data_windows = np.lib.stride_tricks.as_strided(
        data, (len(data) - window_size + 1, window_size), (data.itemsize, data.itemsize)
    )
    percentile = (
        np.sum(data_windows <= data_windows[:, -1][:, None], axis=1)
        / data_windows.shape[1]
    )
    return percentile


def pivoted_df_insert_rows(exit_df: pd.DataFrame, add_df: pd.DataFrame):
    combined_index = exit_df.index.union(add_df.index)
    combined_columns = exit_df.columns.union(add_df.columns)
    add_df_values = add_df.reindex(
        index=combined_index,
        columns=combined_columns,
        fill_value=np.nan,
    ).values
    exit_df_values = exit_df.reindex(
        index=combined_index,
        columns=combined_columns,
        fill_value=np.nan,
    ).values

    return pd.DataFrame(
        np.where(np.isnan(add_df_values), exit_df_values, add_df_values),
        index=combined_index,
        columns=combined_columns,
    )


def load_bench_cons(
    bench_symbol: Literal["000300", "000905", "000852"],
):
    cons_df = pd.read_csv(Path(f"data/cons_of_{bench_symbol}.csv"))
    return cons_df["cons_symbol"].to_list()


def load_hist_data(
    indicator: Literal["rtn", "close", "volume", "volumeRmb"],
    symols: List[int] = None,
    start_date: np.datetime64 = None,
    end_date: np.datetime64 = None,
    hist_985_path: Path = Path(r"data/demo.h5"),
):
    h5db = H5DataBase(hist_985_path)
    data = h5db.load_pivotDF_from_h5data(indicator)
    h5db.f_object_handle.close()
    if symols is not None:
        data = data[symols].copy()
    if start_date is not None:
        data = data[data.index >= start_date]
    if end_date is not None:
        data = data[data.index <= end_date]
    return data


def load_bais(type=Literal["IF", "IC", "IM", "IH"]) -> pd.DataFrame:
    if type == "IF":
        data = "params=%7B%22head%22%3A%22IF%22%2C%22N%22%3A251%7D&PageID=46803&websiteID=20906&ContentID=Content&UserID=&menup=0&_cb=&_cbdata=&_cbExec=1&_cbDispType=1&__pageState=0&__globalUrlParam=%7B%22PageID%22%3A%2246803%22%2C%22pageid%22%3A%2246803%22%7D&g_randomid=randomid_1051095574548506702800710985&np=%5B%2246803%40Content%40TwebCom_div_1_0%40220907102451613%22%5D&modename=amljaGFfZGFpbHlfY2hhcnRfN0Q5MTQ5NDE%3D&creator=cjzq"
    elif type == "IC":
        data = "params=%7B%22head%22%3A%22IC%22%2C%22N%22%3A251%7D&PageID=46803&websiteID=20906&ContentID=Content&UserID=&menup=0&_cb=&_cbdata=&_cbExec=1&_cbDispType=1&__pageState=0&__globalUrlParam=%7B%22PageID%22%3A%2246803%22%2C%22pageid%22%3A%2246803%22%7D&g_randomid=randomid_1051095574548506702800710985&np=%5B%2246803%40Content%40TwebCom_div_1_0%40220907102451613%22%5D&modename=amljaGFfZGFpbHlfY2hhcnRfN0Q5MTQ5NDE%3D&creator=cjzq"
    elif type == "IM":
        data = "params=%7B%22head%22%3A%22IM%22%2C%22N%22%3A251%7D&PageID=46803&websiteID=20906&ContentID=Content&UserID=&menup=0&_cb=&_cbdata=&_cbExec=1&_cbDispType=1&__pageState=0&__globalUrlParam=%7B%22PageID%22%3A%2246803%22%2C%22pageid%22%3A%2246803%22%7D&g_randomid=randomid_1051095574548506702800710985&np=%5B%2246803%40Content%40TwebCom_div_1_0%40220907102451613%22%5D&modename=amljaGFfZGFpbHlfY2hhcnRfN0Q5MTQ5NDE%3D&creator=cjzq"
    elif type == "IH":
        data = "params=%7B%22head%22%3A%22IH%22%2C%22N%22%3A251%7D&PageID=46803&websiteID=20906&ContentID=Content&UserID=&menup=0&_cb=&_cbdata=&_cbExec=1&_cbDispType=1&__pageState=0&__globalUrlParam=%7B%22PageID%22%3A%2246803%22%2C%22pageid%22%3A%2246803%22%7D&g_randomid=randomid_1051095574548506702800710985&np=%5B%2246803%40Content%40TwebCom_div_1_0%40220907102451613%22%5D&modename=amljaGFfZGFpbHlfY2hhcnRfN0Q5MTQ5NDE%3D&creator=cjzq"
    else:
        raise ValueError("type must be one of 'IF', 'IC', 'IM', 'IH'")
    decoded_data = urllib.parse.unquote(data)
    # 解析为字典格式
    parsed_params = urllib.parse.parse_qs(decoded_data)
    parsed_params["g_randomid"] = "randomid_" + str(uuid.uuid4().int)[:-11]
    updated_data = urllib.parse.urlencode(parsed_params, doseq=True)
    response = requests.post(
        "http://web.tinysoft.com.cn:8080/website/loadContentDataAjax.tsl?ref=js",
        updated_data,
    )

    data = response.content.decode("utf-8", "ignore")
    data = json.loads(data)
    soup = BeautifulSoup(data["content"][0]["html"], "html.parser")
    script_content = soup.find("script").string
    match = re.search(r"var\s+SrcData\s*=\s*(\[.*?\]);", script_content, re.DOTALL)
    src_data_raw = match.group(1)
    # 将转义字符转换为实际字符
    src_data = json.loads(src_data_raw.encode().decode("unicode_escape"))
    data_df = pd.DataFrame(src_data)[
        [
            "日期",
            "主力合约",
            "期货价格",
            "现货价格",
            "基差",
            "到期日",
            "剩余天数",
            "期内分红",
            "矫正基差",
            "主力年化基差(%)",
            "年化基差(%)",
        ]
    ]
    # data_df["日期"] = pd.to_datetime(data_df["日期"])
    return data_df
