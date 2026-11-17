"""《深度学习的数学》前两章配套自编实验，不使用原书64张图像数据。

运行: python 最小二乘实验.py
依赖: numpy, matplotlib；不需要GPU、网络或API。
"""
from pathlib import Path
import argparse
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sigmoid(z):
    z = np.asarray(z, dtype=float)
    out = np.empty_like(z)
    pos = z >= 0
    out[pos] = 1 / (1 + np.exp(-z[pos]))
    ez = np.exp(z[~pos])
    out[~pos] = ez / (1 + ez)
    return out


def loss_grad(theta, x, y, activation):
    z = x @ theta[:-1] + theta[-1]
    pred = sigmoid(z) if activation == 'sigmoid' else z
    residual = pred - y
    delta = residual * pred * (1 - pred) if activation == 'sigmoid' else residual
    loss = 0.5 * np.mean(residual ** 2)
    grad = np.r_[x.T @ delta / len(y), np.mean(delta)]
    return float(loss), grad, pred


def gradient_check(theta, x, y, activation):
    _, analytic, _ = loss_grad(theta, x, y, activation)
    numeric = np.zeros_like(theta)
    h = 1e-6
    for i in range(len(theta)):
        plus, minus = theta.copy(), theta.copy()
        plus[i] += h
        minus[i] -= h
        numeric[i] = (loss_grad(plus, x, y, activation)[0] -
                      loss_grad(minus, x, y, activation)[0]) / (2 * h)
    error = float(np.max(np.abs(analytic - numeric)))
    assert error < 1e-6, (activation, error)
    return error


def train(theta, x, y, activation, lr, steps):
    theta = theta.copy()
    history = []
    for step in range(steps + 1):
        loss, grad, pred = loss_grad(theta, x, y, activation)
        history.append([step, loss, *theta])
        if step < steps:
            theta -= lr * grad
    assert np.isfinite(history).all()
    return theta, np.array(history), pred


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[2] /
                        'outputs' / '深度学习的数学前两章')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = {'性质': '自编练习与原表数据复算，非原书网络训练结果'}

    # 实验一：原书2-11的函数，自选初值与三种学习率。
    curves = {}
    for lr in (0.1, 1.0, 1.1):
        point = np.array([1.0, 2.0])
        values = [float(point @ point)]
        for _ in range(30):
            point -= lr * 2 * point
            values.append(float(point @ point))
        curves[lr] = values
    assert curves[0.1][-1] < curves[0.1][0]
    assert np.isclose(curves[1.0][-1], 5)
    assert curves[1.1][-1] > 5
    result['二次函数'] = {str(k): v[-1] for k, v in curves.items()}

    # 实验二：自拟直线，恒等激活。明确采用1/(2N)的平方误差。
    x = np.array([[0.0], [1.0], [2.0]])
    y = np.array([1.0, 3.0, 5.0])
    initial = np.zeros(2)
    check_linear = gradient_check(initial, x, y, 'linear')
    theta, history, pred = train(initial, x, y, 'linear', 0.1, 1000)
    reference = np.linalg.lstsq(np.c_[x, np.ones(len(y))], y, rcond=None)[0]
    assert np.allclose(theta, reference, atol=1e-8)
    assert np.all(np.diff(history[:, 1]) <= 1e-12)
    with (args.output / '直线训练记录.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['迭代次数', '代价J', '权重w', '偏置b'])
        writer.writerows(history)
    result['直线'] = {'初始代价': float(history[0, 1]), '最终代价': float(history[-1, 1]),
                     '权重': float(theta[0]), '偏置': float(theta[1]),
                     '预测': pred.tolist(), '解析参照': reference.tolist(),
                     '梯度差分最大误差': check_linear}

    # 实验三：自拟AND真值表，单Sigmoid单元，使用相同的平方误差目标。
    sx = np.array([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
    sy = np.array([0., 0., 0., 1.])
    start = np.random.default_rng(42).normal(0, 0.1, size=3)
    check_sigmoid = gradient_check(start, sx, sy, 'sigmoid')
    stheta, shistory, spred = train(start, sx, sy, 'sigmoid', 1.0, 20000)
    labels = (spred >= 0.5).astype(int)
    assert np.array_equal(labels, sy)
    result['Sigmoid单元'] = {'初始代价': float(shistory[0, 1]),
                           '最终代价': float(shistory[-1, 1]),
                           '参数': stheta.tolist(), '预测响应': spred.tolist(),
                           '阈值判别': labels.tolist(),
                           '梯度差分最大误差': check_sigmoid,
                           '边界': '仅检查四条训练真值表，不代表真实图像泛化'}

    # 复算2-12原表：第95页的7组数值。
    height = np.array([153.3, 164.9, 168.1, 151.5, 157.8, 156.7, 161.1])
    weight = np.array([45.5, 56.0, 55.0, 52.8, 55.6, 50.8, 56.4])
    design = np.c_[height, np.ones(len(height))]
    pq = np.linalg.lstsq(design, weight, rcond=None)[0]
    c_total = 0.5 * np.sum((design @ pq - weight) ** 2)
    sums = dict(sum_x=float(height.sum()), sum_y=float(weight.sum()),
                sum_x2=float(height @ height), sum_xy=float(height @ weight))
    rounded_pq = np.linalg.solve([[1113.4, 7], [177312, 1113.4]], [372.1, 59274])
    result['原表复算'] = {'p': float(pq[0]), 'q': float(pq[1]),
                         'CT': float(c_total), '原始求和': sums,
                         '按原书取整中间方程求解': rounded_pq.tolist()}

    # 原书第99页/3-4节的三条成绩数据。
    scores = np.array([7., 5., 9.])
    targets = np.array([8., 4., 8.])
    score_pq = np.linalg.lstsq(np.c_[scores, np.ones(3)], targets, rcond=None)[0]
    assert np.allclose(score_pq, [1, -1/3])
    result['三条成绩练习复算'] = score_pq.tolist()
    result['原单元输出复算'] = sigmoid(np.array([-0.3, 1.7])).tolist()
    result['联立数列复算'] = {'初值': [2, 1], '第二项': [7, 5], '第三项': [26, 22]}

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.6), layout='constrained')
    for lr, vals in curves.items():
        axes[0, 0].semilogy(range(31), vals, label=f'learning rate {lr}')
    axes[0, 0].set(title='A. Same function, different learning rates', xlabel='Update', ylabel='x² + y²')
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].semilogy(history[:, 0], np.maximum(history[:, 1], 1e-25))
    axes[0, 1].set(title='B. Linear unit: squared error decreases', xlabel='Update', ylabel='J = mean(error²) / 2')
    axes[1, 0].scatter(x[:, 0], y, s=60, label='Training targets', zorder=3)
    grid = np.linspace(-0.2, 2.2, 50)
    axes[1, 0].plot(grid, theta[0] * grid + theta[1], label='Learned prediction')
    axes[1, 0].set(title='C. Learned w = 2, b = 1', xlabel='Input x', ylabel='Output y')
    axes[1, 0].legend()
    axes[1, 1].plot(shistory[:, 0], shistory[:, 1])
    axes[1, 1].set(title='D. Sigmoid AND unit: squared error', xlabel='Update', ylabel='J')
    for ax in axes.flat:
        ax.grid(alpha=0.2)
    fig.suptitle('Learning parameters by minimizing squared error — supplemental experiments', fontsize=12)
    plot = args.output / '实验结果.png'
    fig.savefig(plot, dpi=150)
    plt.close(fig)
    (args.output / '运行结果.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
