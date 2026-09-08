"""notes/concept/probability/central-limit-theorem.md 的图。

图 1：三种起始分布 × n=1,2,10,50 的标准化平均直方图，叠 N(0,1) 密度（模拟，seed 固定）。
图 2：伯努利和的偏度绝对值随 n 衰减，几条 p；标出 np=5 的位置。
图 3：伯努利和的 sup|F_n − Φ| 实际值（精确二项 CDF 算）与 Berry-Esseen 上界，log-log。
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
from scipy.stats import binom, norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

SEED = 20260908
REPS = 20000
C_BE = 0.4748  # Berry-Esseen 绝对常数目前已证明的上界（Shevtsova 2011）
PLAIN = FuncFormatter(lambda v, _: f"{v:g}")  # 对数轴刻度写成 0.01 / 1 / 100，mathtext 的负号在中文字体里是豆腐块


def plain_log_axis(axis):
    axis.set_major_locator(LogLocator(base=10))
    axis.set_major_formatter(PLAIN)
    axis.set_minor_formatter(NullFormatter())

# ---------------------------------------------------------------- 图 1：形状随 n 变化
rng = np.random.default_rng(SEED)
p_bern = 0.1
sources = [
    ("均匀 U(0,1)，偏度 0", lambda size: rng.uniform(0, 1, size), 0.5, np.sqrt(1 / 12), None),
    ("指数 λ=1，偏度 2", lambda size: rng.exponential(1.0, size), 1.0, 1.0, None),
    (f"伯努利 p={p_bern}，偏度 {(1 - 2 * p_bern) / np.sqrt(p_bern * (1 - p_bern)):.2f}",
     lambda size: rng.binomial(1, p_bern, size), p_bern, np.sqrt(p_bern * (1 - p_bern)), "lattice"),
]
ns = [1, 2, 10, 50]
zs = np.linspace(-4, 4, 400)
phi = norm.pdf(zs)

fig, axes = plt.subplots(len(sources), len(ns), figsize=(13, 8.2), sharex=True)
for r, (label, draw, mu, sd, kind) in enumerate(sources):
    for c, n in enumerate(ns):
        ax = axes[r, c]
        x = draw((REPS, n)).mean(axis=1)
        z = (x - mu) / (sd / np.sqrt(n))
        if kind == "lattice":
            # 平均值只取 k/n，标准化后是等距格点；bin 边界放在格点中点，柱高 = 概率 / 间距，才能和密度比
            step = 1 / (sd * np.sqrt(n))
            k = np.arange(0, n + 1)
            centers = (k / n - mu) / (sd / np.sqrt(n))
            edges = np.concatenate([[centers[0] - step / 2], centers + step / 2])
            ax.hist(z, bins=edges, density=True, color=C_A, alpha=0.75, edgecolor="white", linewidth=0.5)
        else:
            ax.hist(z, bins=45, range=(-4, 4), density=True, color=C_A, alpha=0.75)
        ax.plot(zs, phi, color=C_HI, lw=1.8)
        top = ax.get_ylim()[1]
        ax.set_ylim(0, max(0.55, min(top, 1.15)))
        ax.set_xlim(-4, 4)
        emp_skew = float(np.mean(z ** 3))
        ax.text(0.03, 0.93, f"样本偏度 {emp_skew:.2f}", transform=ax.transAxes, va="top", fontsize=9.5)
        if r == 0:
            ax.set_title(f"n = {n}")
        if c == 0:
            ax.set_ylabel(label, fontsize=10.5)
        if r == len(sources) - 1:
            ax.set_xlabel("标准化平均  Z = (X̄ − μ) / (σ/√n)")
fig.suptitle("标准化平均的分布随 n 增大都趋向同一条曲线 N(0,1)（红线）；起始分布越偏，需要的 n 越大", y=0.995)
fig.tight_layout()
save_jpeg(fig, "central-limit-theorem", "shapes")

# ---------------------------------------------------------------- 图 2：伯努利和的偏度随 n 衰减
ps = [0.5, 0.3, 0.1, 0.02]
colors = [C_GRAY, C_A, C_B, C_HI]
n_grid = np.logspace(0, np.log10(2000), 300)
fig, ax = plt.subplots(figsize=(9, 4.8))
for p, col in zip(ps, colors):
    skew = np.abs(1 - 2 * p) / np.sqrt(n_grid * p * (1 - p))
    ax.plot(n_grid, skew, color=col, lw=2, label=f"伯努利 p = {p}")
    n5 = 5 / p
    s5 = abs(1 - 2 * p) / np.sqrt(n5 * p * (1 - p))
    ax.plot([n5], [s5], "o", color=col, ms=7, zorder=5)
    ax.annotate(f"np=5 → n={n5:.0f}", (n5, s5), textcoords="offset points", xytext=(8, 10), fontsize=9, color=col)
ax.plot(n_grid, 2 / np.sqrt(n_grid), color="black", ls="--", lw=1.2, label="指数分布（偏度 2）作参照")
ax.axhline(1 / np.sqrt(5), color=C_HI, ls=":", lw=1.2, label="1/√5 ≈ 0.447：np = 5 处偏度的上限")
ax.set_xscale("log")
plain_log_axis(ax.xaxis)
ax.set_xlim(1, 2000)
ax.set_ylim(0, 2.2)
ax.set_xlabel("n（对数轴）")
ax.set_ylabel("标准化和的偏度绝对值  |1−2p| / √(np(1−p))")
ax.set_title("偏度按 1/√n 衰减，但起点由 p 决定：p 越接近 0，同样的 n 离正态越远")
ax.legend(loc="upper right")
save_jpeg(fig, "central-limit-theorem", "bernoulli-skewness")


# ---------------------------------------------------------------- 图 3：sup|F_n − Φ| 实际 vs Berry-Esseen 上界
def kolmogorov_gap(n, p):
    """伯努利和的标准化 CDF 与 Φ 的最大偏差。二项 CDF 是阶梯，极值只会出现在跳点处的左右极限。"""
    k = np.arange(0, n + 1)
    zk = (k - n * p) / np.sqrt(n * p * (1 - p))
    f_right = binom.cdf(k, n, p)                 # F(k)
    f_left = np.concatenate([[0.0], f_right[:-1]])  # F(k−)
    ph = norm.cdf(zk)
    return float(max(np.max(np.abs(f_right - ph)), np.max(np.abs(f_left - ph))))


def be_bound(n, p):
    rho_over_sigma3 = (p ** 2 + (1 - p) ** 2) / np.sqrt(p * (1 - p))
    return C_BE * rho_over_sigma3 / np.sqrt(n)


n_pts = np.unique(np.round(np.logspace(0, 4, 40)).astype(int))
fig, ax = plt.subplots(figsize=(9, 4.8))
for p, col in zip([0.5, 0.1, 0.02], [C_GRAY, C_B, C_HI]):
    gaps = [kolmogorov_gap(int(n), p) for n in n_pts]
    ax.plot(n_pts, gaps, "-o", color=col, ms=3.5, lw=1.6, label=f"实际 sup|F_n − Φ|，p = {p}")
    ax.plot(n_pts, [be_bound(n, p) for n in n_pts], "--", color=col, lw=1.2, label=f"Berry-Esseen 上界，p = {p}")
ax.set_xscale("log")
ax.set_yscale("log")
plain_log_axis(ax.xaxis)
plain_log_axis(ax.yaxis)
ax.set_xlabel("n（对数轴）")
ax.set_ylabel("CDF 最大偏差（对数轴）")
ax.set_title("np 够大后误差按 1/√n 下降（斜率 −1/2），p 小时前段是平的；上界松了几倍但斜率一样")
ax.legend(loc="lower left", ncol=2, fontsize=8.5)
save_jpeg(fig, "central-limit-theorem", "berry-esseen")
