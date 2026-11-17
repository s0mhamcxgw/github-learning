
import pandas as pd
import pandas_profiling

# 加载数据
Train_data = pd.read_csv(r'G:\第三周\used_car_train_20200313.csv', sep=' ')

# 创建报告
pfr = pandas_profiling.ProfileReport(
    Train_data,
    title="二手车数据分析报告",
    correlations={
        "auto": {"calculate": True},
        "pearson": {"calculate": True},
        "spearman": {"calculate": True},
        "kendall": {"calculate": True},
        "phi_k": {"calculate": True},
    }
)

# 保存报告
pfr.to_file("./example.html")

print("报告已成功保存为 example.html")
