import pandas as pd
import numpy as np
from WindPy import w

w.start()

begin_date = np.datetime64("2015-01-01")
end_date = np.datetime64("today")
# 801811.SI: 大盘指数(申万)
# 801813.SI: 小盘指数(申万)
# 801823.SI: 低市盈率指数(申万)
# 801821.SI: 高市盈率指数(申万)
# 399371.SZ: 国证价值指数
# 399370.SZ: 国证成长指数
for code in [
    "801811.SI",
    "801813.SI",
    "801823.SI",
    "801821.SI",
    "399371.SZ",
    "399370.SZ",
    "CI013003.WI",  # 招商私募指数股票中性
]:
    _, data = w.wsd(
        code,
        "open,close,high,low,volume,amt,turn,chg,pct_chg",
        np.datetime_as_string(begin_date, unit="D"),
        np.datetime_as_string(end_date, unit="D"),
        PriceAdj="F",
        usedf=True,
    )
    data.index.name = "日期"
    data.reset_index(drop=False, inplace=True)
    data.to_csv(rf"data/{code}.csv", index=False, encoding="utf_8_sig")

code_sw1 = [
    "801010.SI",
    "801030.SI",
    "801040.SI",
    "801050.SI",
    "801080.SI",
    "801110.SI",
    "801120.SI",
    "801130.SI",
    "801140.SI",
    "801150.SI",
    "801160.SI",
    "801170.SI",
    "801180.SI",
    "801200.SI",
    "801210.SI",
    "801230.SI",
    "801710.SI",
    "801720.SI",
    "801730.SI",
    "801740.SI",
    "801750.SI",
    "801760.SI",
    "801770.SI",
    "801780.SI",
    "801790.SI",
    "801880.SI",
    "801890.SI",
    "801950.SI",
    "801960.SI",
    "801970.SI",
    "801980.SI",
]

for code in code_sw1:
    _, data = w.wsd(
        code,
        "open,close,high,low,volume,amt,turn,chg,pct_chg",
        np.datetime_as_string(begin_date, unit="D"),
        np.datetime_as_string(end_date, unit="D"),
        PriceAdj="F",
        usedf=True,
    )
    data.index.name = "日期"
    data.reset_index(drop=False, inplace=True)
    data.to_csv(rf"data/sw1/{code}.csv", index=False, encoding="utf_8_sig")

# wind 全A情况
_, data = w.wsd(
    "881001.WI",
    "open,close,high,low,volume,amt,turn,chg,pct_chg,free_float_shares",
    np.datetime_as_string(begin_date, unit="D"),
    np.datetime_as_string(end_date, unit="D"),
    PriceAdj="F",
    usedf=True,
)
data.index.name = "日期"
data.reset_index(drop=False, inplace=True)
data.to_csv(rf"data/881001.WI.csv", index=False, encoding="utf_8_sig")
