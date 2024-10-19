import akshare as ak
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Literal

bench_load_dict = {
    # 中证指数
    "000300": ak.stock_zh_index_hist_csindex,
    "000905": ak.stock_zh_index_hist_csindex,
    "000852": ak.stock_zh_index_hist_csindex,
    # 国证指数
    "399370": ak.index_hist_cni,  # 国证价值
    "399371": ak.index_hist_cni,  # 国证价值
}


def load_bench_hist(
    func,
    bench_symbol: Literal["000300", "000905", "000852"],
) -> pd.DataFrame:
    hist_df = func(
        symbol=bench_symbol,
        start_date=(datetime.now() - timedelta(days=3 * 365)).strftime("%Y%m%d"),
        end_date=datetime.now().strftime("%Y%m%d"),
    )
    hist_df.to_csv(
        Path(f"data/hist_of_{bench_symbol}.csv"), index=False, encoding="utf-8-sig"
    )


ak.index_hist_cni(
    symbol="399371",
    start_date=(datetime.now() - timedelta(days=2 * 365)).strftime("%Y%m%d"),
    end_date=datetime.now().strftime("%Y%m%d"),
)

if __name__ == "__main__":
    for symbol_i, func in bench_load_dict.items():
        load_bench_hist(func, symbol_i)
