# ---------------------- 导入必要的库 ----------------------
import torch  # PyTorch 基础库
import torch.nn as nn  # 神经网络组件
from torch.nn.utils.rnn import pad_sequence  # 带补的序列编辑功能
from torch.utils.data import Dataset, DataLoader  # 数据集和输入管道
from transformers import BertTokenizer, BertModel  # Huggingface 中 BERT 的切分器和模型
from sklearn import metrics  # sklearn 评价指标
import pandas as pd  # 数据表格操作
import argparse  # 命令行参数解析
import os  # 操作系统操作

from utils import load_corpus, load_corpus_bert, stopwords  # 自定义函数，包括读文本和停用词处理

# ---------------------- 解析命令行参数 ----------------------
parser = argparse.ArgumentParser(description="BERT + CNN 情感分类器")
parser.add_argument('--mode', choices=['train', 'test'], required=True, help='运行模式: train or test')
parser.add_argument('--model_path', type=str, default='./model/cnn_bert_final.model', help='模型保存/加载路径')
parser.add_argument('--epochs', type=int, default=5, help='训练轮数')
parser.add_argument('--batch_size', type=int, default=24, help='批处理大小')
parser.add_argument('--lr', type=float, default=5e-4, help='学习率')
args = parser.parse_args()

# ---------------------- 设置设备和超参 ----------------------
device = "cuda:0" if torch.cuda.is_available() else "cpu"  # 如果有GPU就用GPU
num_filters = 128  # 每个卷积核的输出速度
filter_sizes = [2, 3, 4]  # 卷积核的尺寸（bi-gram，tri-gram...）
max_length = 128  # BERT 输入最大长度

# ---------------------- 加载 BERT 切分器和预训练模型 ----------------------
tokenizer = BertTokenizer.from_pretrained('./bert_base_uncased')  # 切分器
bert_model = BertModel.from_pretrained('./bert_base_uncased').to(device)  # 模型加载并上传到 GPU

# ---------------------- 读取数据 ----------------------
TRAIN_PATH = "./data/ChnSentiCorp_htl_all/train.csv"
DEV_PATH = "./data/ChnSentiCorp_htl_all/dev.csv"
TEST_PATH = "./data/ChnSentiCorp_htl_all/test.csv"
train_data =load_corpus_bert(TRAIN_PATH)
dev_data =load_corpus_bert(DEV_PATH)
test_data =load_corpus_bert(TEST_PATH)

# TRAIN_PATH = "./data/weibo2018/train.txt"
# DEV_PATH = "./data/weibo2018/test.txt"
# TEST_PATH = "./data/weibo2018/test.txt"
# train_data = load_corpus(TRAIN_PATH)
# dev_data = load_corpus(DEV_PATH)
#test_data = load_corpus(TEST_PATH)
df_train = pd.DataFrame(train_data, columns=["text", "label"])
df_dev = pd.DataFrame(dev_data, columns=["text", "label"])
df_test = pd.DataFrame(test_data, columns=["text", "label"])

# ---------------------- 自定义 Dataset 数据类 ----------------------
class MyDataset(Dataset):
    def __init__(self, df):
        self.data = []
        self.label = df["label"].tolist()
        for s in df["text"].tolist():
            inputs = tokenizer(s, padding=True, truncation=True, return_tensors="pt", max_length=max_length)
            self.data.append(inputs)

    def __getitem__(self, index):
        return self.data[index], float(self.label[index])  # 返回 token 和 label

    def __len__(self):
        return len(self.label)  # 数据的长度

# ---------------------- 定义 collate_fn 合并数据批 ----------------------
def collate_fn(data):
    input_ids = [item[0]['input_ids'].squeeze(0) for item in data]
    attention_mask = [item[0]['attention_mask'].squeeze(0) for item in data]
    labels = [item[1] for item in data]
    input_ids = pad_sequence(input_ids, batch_first=True, padding_value=tokenizer.pad_token_id)
    attention_mask = pad_sequence(attention_mask, batch_first=True, padding_value=0)
    return input_ids, attention_mask, torch.tensor(labels)

# ---------------------- 创建数据输入模块 ----------------------
train_loader = DataLoader(MyDataset(df_train), batch_size=args.batch_size, collate_fn=collate_fn, shuffle=True)
test_loader = DataLoader(MyDataset(df_test), batch_size=args.batch_size, collate_fn=collate_fn, shuffle=False)

# ---------------------- BERT + CNN 模型 ----------------------
class BERT_CNN(nn.Module):
    def __init__(self, filter_sizes, num_filters):
        super(BERT_CNN, self).__init__()
        self.bert = bert_model
        for param in self.bert.parameters():
            param.requires_grad = False  # 冻结 BERT

        # 构造多个卷积层，根据不同核尺寸
        self.convs = nn.ModuleList([
            nn.Conv2d(1, num_filters, (k, 768)) for k in filter_sizes
        ])
        self.dropout = nn.Dropout(0.5)  # 防止过拟合
        self.fc = nn.Linear(num_filters * len(filter_sizes), 1)  # 全连
        self.sigmoid = nn.Sigmoid()  # 二分类

    def forward(self, input_ids, attention_mask):
        with torch.no_grad():
            outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
            x = outputs.last_hidden_state  # (batch_size, seq_len, 768)

        x = x.unsqueeze(1)  # 增加通道维 (batch_size, 1, seq_len, 768)
        x = [torch.relu(conv(x)).squeeze(3) for conv in self.convs]  # 卷积 -> ReLU -> squeeze
        x = [torch.max(pooled, dim=2)[0] for pooled in x]  # max pooling
        x = torch.cat(x, dim=1)  # 拼接各个 filter 输出
        x = self.dropout(x)  # 防止过拟合
        x = self.fc(x)  # 全连层
        return self.sigmoid(x)

# ---------------------- 模型评价函数 ----------------------
def evaluate(model, data_loader):
    model.eval()
    y_pred, y_true = [], []
    with torch.no_grad():
        for input_ids, attention_mask, labels in data_loader:
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device).float()
            outputs = model(input_ids, attention_mask).view(-1)
            y_pred.append(outputs)
            y_true.append(labels)

    y_prob = torch.cat(y_pred)
    y_true = torch.cat(y_true)
    y_label = (y_prob > 0.5).float()

    print(metrics.classification_report(y_true.cpu(), y_label.cpu()))
    print("Accuracy:", metrics.accuracy_score(y_true.cpu(), y_label.cpu()))
    print("AUC:", metrics.roc_auc_score(y_true.cpu(), y_prob.cpu()))

# ---------------------- 训练函数 ----------------------
def train():
    model = BERT_CNN(filter_sizes, num_filters).to(device)
    criterion = nn.BCELoss()  # 二分类与 sigmoid 配套的损失函数
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        model.train()
        total_loss = 0
        for i, (input_ids, attention_mask, labels) in enumerate(train_loader):
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device).float()

            outputs = model(input_ids, attention_mask).view(-1)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            if (i + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}, Step {i + 1}, Loss: {total_loss / 10:.4f}")
                total_loss = 0

        print(f"[Epoch {epoch+1}] Testing on validation set:")
        evaluate(model, test_loader)

        os.makedirs(os.path.dirname(args.model_path), exist_ok=True)
        torch.save(model.state_dict(), args.model_path)
        print(f"Model saved to {args.model_path}")

# ---------------------- 模型测试函数 ----------------------
def test():
    model = BERT_CNN(filter_sizes, num_filters).to(device)
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    evaluate(model, test_loader)

# ---------------------- 主程序运行入口 ----------------------
if __name__ == '__main__':
    if args.mode == 'train':
        train()
    elif args.mode == 'test':
        test()
