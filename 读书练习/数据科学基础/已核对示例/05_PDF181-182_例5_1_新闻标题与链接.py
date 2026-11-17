# 说明：按扫描页重排、规范排版标点与提示语；不是出版社源代码文件。
# 来源：《数据科学基础》PDF第182页。
# 状态：对照原图校正；离线HTML夹具验证通过；真实网站未验证。
# 本代码依赖原书成书时的网页结构/网络；离线测试通过不代表今天的网站仍适用。

import requests
from bs4 import BeautifulSoup

# 爬取网页
url = "http://news.baidu.com"
response = requests.get(url)
# 解析网页
soup = BeautifulSoup(response.text, "html.parser")
# 定位 div hotnews
divs = soup.find("div", class_="hotnews")
for n in range(0, 5):
    # 定位 a 标签
    a = divs.find("li", class_="hdline{}".format(n)).find("a")
    # 爬取新闻标题、链接
    title = a.get_text()
    href = a.get("href")
    # 写入文件
    with open("hotnews.txt", "a", encoding="utf-8") as f:
        f.write("标题：" + title + "\n")
        f.write("链接：" + href + "\n")
