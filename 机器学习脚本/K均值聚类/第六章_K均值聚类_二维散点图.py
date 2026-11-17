# -*- coding: utf-8 -*-
"""
《数据科学基础》第六章 —— K 均值聚类：二维空间散点图可视化
包含两部分：
  A. 书中原文（PDF 第 308 页）：用 seaborn 画出 iris 数据前两列的散点图
  B. 聚类结果可视化（补充）：把 K 均值聚类结果用散点图画出，
     不同簇用不同颜色，并把簇中心（质心）标出来

依赖：numpy、pandas、matplotlib、seaborn、scikit-learn
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 复用第六章 kMeans 算法（若与本文件同目录，直接 import；否则按需调整）
from sklearn.datasets import load_iris


# ----------------------------------------------------------------------
# A. 书中原文（PDF 第 308 页）
#    画出 iris 数据，取数据的前两列在二维空间画散点图
# ----------------------------------------------------------------------
def plot_iris_seaborn():
    sns.set()

    # 原书是读取本地 csv：iris = pd.read_csv('..\\data\\iris.csv')
    # 这里改用 sklearn 内置 iris 数据，方便直接运行
    iris = load_iris()
    df = pd.DataFrame(iris.data, columns=['sepal_length', 'sepal_width',
                                          'petal_length', 'petal_width'])
    df['species'] = [iris.target_names[i] for i in iris.target]

    # 画出前两列（花萼长度 × 花萼宽度）的散点图，按品种着色
    sns.scatterplot(x='sepal_length', y='sepal_width', hue='species',
                    data=df, style='species')
    plt.title('Iris 数据前两列散点图（seaborn）')
    plt.show()


# ----------------------------------------------------------------------
# B. 聚类结果可视化（补充）
#    把 K 均值聚类结果画成二维散点图：不同簇用不同颜色，并标出簇中心
# ----------------------------------------------------------------------
def plot_kmeans_result():
    from sklearn.cluster import KMeans

    iris = load_iris()
    X = iris.data
    y = iris.target

    # 只取前两个特征（sepal_length, sepal_width），便于画到二维平面上
    X2 = X[:, :2]

    # 用 sklearn 的 KMeans 聚类（k=3）
    km = KMeans(n_clusters=3, n_init=10, random_state=0)
    km.fit(X2)
    labels = km.labels_          # 每个样本所属的簇号
    centroids = km.cluster_centers_   # 3 个簇中心（二维坐标）

    # 画散点图：按聚类结果着色
    plt.figure(figsize=(8, 6))
    plt.scatter(X2[:, 0], X2[:, 1], c=labels, cmap='viridis',
                s=50, alpha=0.8, edgecolors='k')
    # 标出簇中心
    plt.scatter(centroids[:, 0], centroids[:, 1], c='red',
                marker='x', s=200, linewidths=3, label='簇中心')
    plt.xlabel('sepal length (cm)')
    plt.ylabel('sepal width (cm)')
    plt.title('K 均值聚类结果（k=3，前两维）')
    plt.legend()
    plt.show()


# 如果你想用「自定义 kMeans 函数」来画（而不是 sklearn 的 KMeans），
# 把第六章文件里的 distEclud / randCent / kMeans 三个函数复制过来后，
# 把 plot_kmeans_result() 里的 sklearn 调用替换成：
#     mycent, clustAssment = kMeans(X2, 3)
#     labels = clustAssment[:, 0].astype(int)
#     centroids = np.array(mycent)
# 即可画出同样的效果。


if __name__ == '__main__':
    plot_iris_seaborn()
    plot_kmeans_result()
