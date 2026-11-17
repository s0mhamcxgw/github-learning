import jieba  #jieba: 中文分词工具；
import re  # 正则表达式，用于文本清洗；
import csv
from collections import Counter
from wordcloud import WordCloud  #用于生成词云；
import matplotlib.pyplot as plt

# ===================== 文本预处理函数 =====================
def processing(text):
    """
    数据预处理, 可以根据自己的需求进行重载
    """
    # 数据清洗部分
    text = re.sub("\{%.+?%\}", " ", text)           # 去除 {%xxx%} 模板标签（如地理定位、微博话题等）
    text = re.sub("@.+?( |$)", " ", text)           # 去除 @用户名 形式内容
    text = re.sub("【.+?】", " ", text)              # 去除 【】括起来的内容（通常是转发或来源信息）
    text = re.sub("\u200b", " ", text)              # 去除不可见字符 \u200b（零宽空格）

    # 分词，只保留纯字母/汉字词  使用 jieba.lcut() 进行精确分词，并仅保留纯字母/汉字词语（去除标点、数字等）。
    words = [w for w in jieba.lcut(text) if w.isalpha()]

    # 否定词“不”与后一个词拼接，如“不好”
    while "不" in words:
        index = words.index("不")
        if index < len(words) - 1:
            words[index:index+2] = ["".join(words[index:index+2])]
        else:
            break

    #  将“不 + 形容词或动词”合并为一个词（如“不好”“不是”等），保留其语义完整性，有助于后续词频统计。

    return " ".join(words)
    # 返回处理结果，将词语用空格拼接成一整段字符串，便于后续统计词频。

# ===================== 文件读取与数据处理 =====================
# 数据路径
csv_path = "./data/ChnSentiCorp_htl_all/test.csv"

# 存储处理后的文本
data = []

# 读取CSV文件（假设每行：label,text）
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) < 2:
            continue  # 跳过格式不完整的行
        sentiment = row[0]
        content = row[1]
        cleaned = processing(content)
        data.append(cleaned)

# 合并所有文本为一个字符串
all_text = " ".join(data)

# 按空格分词
words = all_text.split()

# ===================== 词频统计 =====================
# 使用Counter统计词频
word_counts = Counter(words)

# 自定义停用词列表
stopwords = set([
    "正是","而是","我们","那里","你们","如今", "说道","知道","老太太","起来","姑娘",
    "这里","出来","他们","众人","自己","一面","太太", "只见","怎么","奶奶","两个",
    "没有","不是","不知","这个","听见"
])

# 过滤停用词
for stop in stopwords:
    word_counts.pop(stop, None)

# 只保留前100个高频词
top_words = dict(word_counts.most_common(100))

# ===================== 生成词云图 =====================
# 创建词云对象
wc = WordCloud(
    font_path="C:/Windows/Fonts/simhei.ttf",  # ✅ 确保该字体文件存在，适用于Windows中文显示
    background_color="white",
    width=800,
    height=600,
    max_font_size=80
)

# 生成词云图
wc.generate_from_frequencies(top_words)

# 显示词云图
plt.figure(figsize=(10, 8))
plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
plt.tight_layout()
plt.show()

# 保存图片到文件
wc.to_file("情感词云图.jpg")
