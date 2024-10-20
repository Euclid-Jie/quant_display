import akshare as ak
import pandas as pd
import numpy as np
from pathlib import Path
from utils import now_time, pivoted_df_insert_rows
from H5DataBase import H5DataBase
from datetime import datetime, timedelta
from typing import Literal, List
import concurrent.futures

bench_hist_load_dict = {
    # 中证指数
    "000300": ak.stock_zh_index_hist_csindex,
    "000905": ak.stock_zh_index_hist_csindex,
    "000852": ak.stock_zh_index_hist_csindex,
    # 国证指数
    "399370": ak.index_hist_cni,  # 国证价值
    "399371": ak.index_hist_cni,  # 国证价值
}


def load_bench_cons_csindex(bench_symbol: Literal["000300", "000905", "000852"]):
    "中证指数成分股"
    data = ak.index_stock_cons_csindex(symbol=bench_symbol)
    cons_df = data.copy().rename(
        columns={"指数代码": "symbol", "成分券代码": "cons_symbol"}
    )[["symbol", "cons_symbol"]]
    cons_df["update_time"] = now_time()
    cons_df.to_csv(
        Path(f"data/cons_of_{bench_symbol}.csv"), index=False, encoding="utf-8-sig"
    )


def load_bench_hist(
    func,
    bench_symbol: Literal["000300", "000905", "000852"],
) -> pd.DataFrame:
    hist_df = func(
        symbol=bench_symbol,
        start_date=(datetime.now() - timedelta(days=3 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    hist_df["update_time"] = now_time()
    hist_df.to_csv(
        Path(f"data/hist_of_{bench_symbol}.csv"), index=False, encoding="utf-8-sig"
    )


def update_hist_em(hist_985_path: Path = Path(r"data/hist_985.h5")):
    h5db = H5DataBase(hist_985_path)
    rtn = h5db.load_pivotDF_from_h5data("rtn")
    close = h5db.load_pivotDF_from_h5data("close")
    volume = h5db.load_pivotDF_from_h5data("volume")
    volumeRmb = h5db.load_pivotDF_from_h5data("volumeRmb")
    h5db.f_object_handle.close()

    symbol = [str(i).zfill(6) for i in rtn.columns.to_list()]
    # load data from em
    print("Updating data from em...")
    data = pd.DataFrame()
    start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
    end_date = datetime.now().strftime("%Y%m%d")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = []
        for symbol_i in symbol:
            results.append(
                executor.submit(
                    _update_single_hist_em,
                    symbol_i,
                    start_date,
                    end_date,
                )
            )

        for future in concurrent.futures.as_completed(results):
            data = pd.concat([data, future.result()])

        data["日期"] = pd.to_datetime(data["日期"])
        data["股票代码"] = data["股票代码"].astype(int)
        data["涨跌幅"] = data["涨跌幅"] / 100

        # rtn
        add_rtn = data.pivot(index="日期", columns="股票代码", values="涨跌幅")
        add_rtn = add_rtn.astype("float32")
        new_rtn = pivoted_df_insert_rows(rtn, add_rtn)
        H5DataBase.write_pivotDF_to_h5data(
            h5FilePath=hist_985_path,
            pivotDF=new_rtn,
            pivotKey="rtn",
            rewrite=True,
        )

        # close
        add_close = data.pivot(index="日期", columns="股票代码", values="收盘")
        add_close = add_close.astype("float32")
        new_close = pivoted_df_insert_rows(close, add_close)
        H5DataBase.add_pivotDF_to_h5data(
            h5FilePath=hist_985_path,
            pivotDF=new_close,
            pivotKey="close",
        )

        # volume
        add_volume = data.pivot(index="日期", columns="股票代码", values="成交量")
        add_volume = add_volume.astype("float32")
        new_volume = pivoted_df_insert_rows(volume, add_volume)
        H5DataBase.add_pivotDF_to_h5data(
            h5FilePath=hist_985_path,
            pivotDF=new_volume,
            pivotKey="volume",
        )

        # volumeRmb
        add_volumeRmb = data.pivot(index="日期", columns="股票代码", values="成交额")
        add_volumeRmb = add_volumeRmb.astype("float32")
        new_volumeRmb = pivoted_df_insert_rows(volumeRmb, add_volumeRmb)
        H5DataBase.add_pivotDF_to_h5data(
            h5FilePath=hist_985_path,
            pivotDF=new_volumeRmb,
            pivotKey="volumeRmb",
        )
    return data


def _update_single_hist_em(symbol: str, start_date: str, end_date: str):
    assert len(symbol) == 6, "symbol must be 6 digits"
    data = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="",
    )
    return data


if __name__ == "__main__":
    print("Updating daily data...")
    # 指数成分股,  仅支持中证指数
    for symbol_i in ["000300", "000905", "000852"]:
        load_bench_cons_csindex(symbol_i)

    # 指数daliy行情
    for symbol_i, func in bench_hist_load_dict.items():
        load_bench_hist(func, symbol_i)

    # # 更新中证全指数行情
    # update_hist_em(hist_985_path=Path(r"data/demo.h5"))
