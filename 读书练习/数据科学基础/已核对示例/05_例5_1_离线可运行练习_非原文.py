# 说明：按扫描页重排、规范排版标点与提示语；不是出版社源代码文件。
# 来源：《数据科学基础》PDF第182页。
# 状态：学习改写（非原文）；本机实际运行通过；无需网络。

from pathlib import Path
from bs4 import BeautifulSoup

# 学习改写（非原文）：用随附的本地HTML练习原书的标签定位方法。
base = Path(__file__).resolve().parent
html = (base / "fixtures" / "新闻示例.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")
divs = soup.find("div", class_="hotnews")
rows = []
for n in range(5):
    a = divs.find("li", class_="hdline{}".format(n)).find("a")
    rows.append((a.get_text(), a.get("href")))
output = base / "运行结果"
output.mkdir(exist_ok=True)
with (output / "新闻结果.txt").open("w", encoding="utf-8") as f:
    for title, href in rows:
        print(title, href)
        f.write("标题：" + title + "\n链接：" + href + "\n")
print("结果已保存到：", output / "新闻结果.txt")
