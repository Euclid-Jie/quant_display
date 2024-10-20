from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
from pathlib import Path
from H5DataBase import H5DataBase
from datetime import datetime
from typing import Literal, List

__all__ = ["now_time", "pivoted_df_insert_rows", "load_hist_data", "load_bench_cons"]


def now_time():
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


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
