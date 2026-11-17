import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel
from sklearn import metrics
import pandas as pd
from torch.nn.utils.rnn import pad_sequence
from utils import load_corpus, load_corpus_bert, stopwords  # 自定义函数，包括读文本和停用词处理
import argparse
import os

# 设置设备
device = "cuda:0" if torch.cuda.is_available() else "cpu"

# 参数解析器
parser = argparse.ArgumentParser()
parser.add_argument('--mode', type=str, choices=['train', 'test'], default='train', help='运行模式：train 或 test')
parser.add_argument('--epochs', type=int, default=5, help='训练轮数')
parser.add_argument('--batch_size', type=int, default=24, help='批大小')
parser.add_argument('--lr', type=float, default=5e-4, help='学习率')
parser.add_argument('--model_path', type=str, default='./model/lstm_bert_final.model', help='保存或加载模型路径')
args = parser.parse_args()

# 超参数
learning_rate = args.lr
num_epoches = args.epochs
batch_size = args.batch_size
hidden_size = 64
num_layers = 2
max_length = 128

# 加载BERT
tokenizer = BertTokenizer.from_pretrained('./bert_base_uncased')
bert_model = BertModel.from_pretrained('./bert_base_uncased').to(device)

# 加载数据
TRAIN_PATH = "./data/ChnSentiCorp_htl_all/train.csv"
DEV_PATH = "./data/ChnSentiCorp_htl_all/dev.csv"
TEST_PATH = "./data/ChnSentiCorp_htl_all/test.csv"
train_data =load_corpus_bert(TRAIN_PATH)
dev_data =load_corpus_bert(DEV_PATH)
test_data =load_corpus_bert(TEST_PATH)

if args.mode == 'train':
    df_train = pd.DataFrame(train_data + dev_data, columns=["text", "label"])
elif args.mode == 'test':
    df_test = pd.DataFrame(test_data, columns=["text", "label"])

class MyDataset(Dataset):
    def __init__(self, df):
        self.data = []
        self.label = df["label"].tolist()
        for s in df["text"].tolist():
            inputs = tokenizer(s, padding=True, truncation=True, return_tensors="pt", max_length=max_length)
            self.data.append(inputs)

    def __getitem__(self, index):
        inputs = self.data[index]
        label = float(self.label[index])
        return inputs, label

    def __len__(self):
        return len(self.label)

def collate_fn(data):
    input_ids = [item[0]['input_ids'].squeeze(0) for item in data]
    attention_mask = [item[0]['attention_mask'].squeeze(0) for item in data]
    labels = [item[1] for item in data]
    input_ids = pad_sequence(input_ids, batch_first=True, padding_value=tokenizer.pad_token_id)
    attention_mask = pad_sequence(attention_mask, batch_first=True, padding_value=0)
    return input_ids, attention_mask, torch.tensor(labels)

class LSTM(nn.Module):
    def __init__(self, hidden_size, num_layers):
        super(LSTM, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size=768, hidden_size=hidden_size, num_layers=num_layers, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(hidden_size * 2, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, input_ids, attention_mask):
        with torch.no_grad():
            outputs = bert_model(input_ids=input_ids, attention_mask=attention_mask)
            cls_embedding = outputs.last_hidden_state[:, 0, :]
        h0 = torch.zeros(self.num_layers * 2, input_ids.size(0), self.hidden_size).to(device)
        c0 = torch.zeros(self.num_layers * 2, input_ids.size(0), self.hidden_size).to(device)
        lstm_out, (h_n, h_c) = self.lstm(cls_embedding.unsqueeze(1), (h0, c0))
        lstm_out = torch.cat([h_n[-2], h_n[-1]], 1)
        out = self.fc(lstm_out)
        return self.sigmoid(out)

lstm = LSTM(hidden_size, num_layers).to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.Adam(lstm.parameters(), lr=learning_rate)

def evaluate(data_loader):
    y_pred, y_true = [], []
    lstm.eval()
    with torch.no_grad():
        for input_ids, attention_mask, labels in data_loader:
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device).float()
            outputs = lstm(input_ids, attention_mask).view(-1)
            y_pred.append(outputs)
            y_true.append(labels)
    y_prob = torch.cat(y_pred)
    y_true = torch.cat(y_true)
    y_pred = y_prob.clone()
    y_pred[y_pred > 0.5] = 1
    y_pred[y_pred <= 0.5] = 0
    print(metrics.classification_report(y_true, y_pred))
    print("Accuracy:", metrics.accuracy_score(y_true, y_pred))
    print("AUC:", metrics.roc_auc_score(y_true, y_prob))

if args.mode == 'train':
    train_dataset = MyDataset(df_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=True)
    for epoch in range(num_epoches):
        lstm.train()
        total_loss = 0
        for i, (input_ids, attention_mask, labels) in enumerate(train_loader):
            input_ids = input_ids.to(device)
            attention_mask = attention_mask.to(device)
            labels = labels.to(device).float()
            outputs = lstm(input_ids, attention_mask).view(-1)
            loss = criterion(outputs, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            if (i + 1) % 10 == 0:
                print(f"Epoch {epoch + 1}, Step {i + 1}, Loss: {total_loss / 10:.4f}")
                total_loss = 0
        torch.save(lstm.state_dict(), args.model_path)
        print(f"Model saved to {args.model_path}")
        print("Evaluation on training set:")
        evaluate(train_loader)

elif args.mode == 'test':
    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"Model file not found: {args.model_path}")
    lstm.load_state_dict(torch.load(args.model_path, map_location=device))
    df_test = pd.DataFrame(test_data, columns=["text", "label"])
    test_dataset = MyDataset(df_test)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=False)
    print("Evaluation on test set:")
    evaluate(test_loader)