from typing import Literal
from bs4 import BeautifulSoup
import requests
import re
import urllib.parse
import json
import uuid
import pandas as pd


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
    data_df["日期"] = pd.to_datetime(data_df["日期"])
    return data_df
