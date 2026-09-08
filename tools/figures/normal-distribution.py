"""notes/concept/probability/normal-distribution.md 的图。

图 1：Bin(n, p) 标准化后与 N(0,1) 叠加，n = 5 / 20 / 100，看形状怎么收敛（de Moivre–Laplace）。
图 2：N(0,1) 密度上标 ±1σ / ±2σ / ±3σ 区域面积（68-95-99.7 的精确值）。
图 3：同一族分布换 μ、换 σ 形状怎么变：μ 只平移，σ 决定宽度与峰高 1/(σ√(2π))。
所有数值用 scipy 算，不手填。
"""
import sys
from math import pi, sqrt
from pathlib import Path

import numpy as np
from scipy.stats import binom, norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

NOTE = "normal-distribution"
xs = np.linspace(-4, 4, 801)
phi = norm.pdf(xs)

# ---- 图 1：二项标准化后逼近 N(0,1) ----
p = 0.3
fig, axes = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
for ax, n in zip(axes, (5, 20, 100)):
    mu, sd = n * p, sqrt(n * p * (1 - p))
    ks = np.arange(n + 1)
    z = (ks - mu) / sd                       # 标准化后的取值位置
    dens = binom.pmf(ks, n, p) * sd          # 概率质量 ÷ 柱宽(1/sd) = 密度尺度，才能和曲线比
    keep = dens > 1e-4
    ax.bar(z[keep], dens[keep], width=1 / sd, color=C_A, alpha=0.65, edgecolor="white", lw=0.5,
           label=f"Bin({n}, {p}) 标准化")
    ax.plot(xs, phi, color=C_HI, lw=2, label="N(0, 1) 密度")
    skew = (1 - 2 * p) / sd
    ax.set_title(f"n = {n}：偏度 {skew:.2f}", fontsize=12)
    ax.set_xlabel("z = (X − np) / √(np(1−p))")
    ax.set_xlim(-4, 4)
    ax.set_ylim(0, 0.5)
    ax.legend(loc="upper right", fontsize=9)
axes[0].set_ylabel("密度")
fig.suptitle("二项分布标准化后，n 越大越贴近同一条钟形曲线（p = 0.3，柱高 = 概率 × 标准差）", y=1.03)
save_jpeg(fig, NOTE, "binomial-to-normal")

# ---- 图 2：68-95-99.7 ----
bands = [(3, "#DCE4F2"), (2, "#A9BCE0"), (1, C_A)]   # 从外到内，深色盖在浅色上
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.plot(xs, phi, color="black", lw=1.8)
for k, col in bands:
    m = np.abs(xs) <= k
    ax.fill_between(xs[m], phi[m], color=col, alpha=0.95)
probs = {k: norm.cdf(k) - norm.cdf(-k) for k in (1, 2, 3)}
ax.annotate(f"|Z| ≤ 1：{probs[1] * 100:.2f}%", xy=(0, 0.16), ha="center", fontsize=11, color="white", weight="bold")
ax.annotate(f"1 < |Z| ≤ 2\n两侧合计 {(probs[2] - probs[1]) * 100:.2f}%", xy=(-1.5, 0.07), xytext=(-2.9, 0.19),
            ha="center", fontsize=9.5, color="#1F3C73", arrowprops=dict(arrowstyle="-", color=C_GRAY, lw=0.8))
ax.annotate(f"2 < |Z| ≤ 3\n两侧合计 {(probs[3] - probs[2]) * 100:.2f}%", xy=(2.55, 0.011), xytext=(2.9, 0.16),
            ha="center", fontsize=9.5, color="#1F3C73", arrowprops=dict(arrowstyle="-", color=C_GRAY, lw=0.8))
ax.annotate(f"|Z| > 3\n两侧合计 {(1 - probs[3]) * 100:.2f}%", xy=(3.2, 0.004), xytext=(3.5, 0.06), ha="center",
            fontsize=9.5, color=C_HI, arrowprops=dict(arrowstyle="->", color=C_HI, lw=0.8))
for k in (1, 2, 3):
    for s in (-k, k):
        ax.axvline(s, color=C_GRAY, ls=":", lw=0.9)
ax.set_xticks(range(-4, 5), [f"μ{v:+d}σ" if v else "μ" for v in range(-4, 5)])
ax.set_xlim(-4, 4)
ax.set_ylim(0, 0.43)
ax.set_ylabel("密度")
ax.set_title(f"经验法则的精确值：±1σ 内 {probs[1]:.4f}，±2σ 内 {probs[2]:.4f}，±3σ 内 {probs[3]:.4f}")
save_jpeg(fig, NOTE, "empirical-rule")

# ---- 图 3：换 μ 与换 σ ----
xw = np.linspace(-7, 7, 1401)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for mu, col in zip((-2, 0, 2), (C_A, C_GRAY, C_B)):
    ax1.plot(xw, norm.pdf(xw, mu, 1), color=col, lw=2, label=f"μ = {mu}, σ = 1")
    ax1.axvline(mu, color=col, ls=":", lw=0.9)
ax1.set_title("换 μ：整条曲线平移，形状不变")
ax1.set_xlabel("x")
ax1.set_ylabel("密度")
ax1.legend(loc="upper left", fontsize=9)
for sd, col in zip((0.5, 1, 2), (C_HI, C_GRAY, C_A)):
    ax2.plot(xw, norm.pdf(xw, 0, sd), color=col, lw=2, label=f"μ = 0, σ = {sd}")
    peak = 1 / (sd * sqrt(2 * pi))
    ax2.annotate(f"峰高 1/(σ√2π) = {peak:.3f}", xy=(0, peak), xytext=(2.3, peak), fontsize=9, color=col,
                 arrowprops=dict(arrowstyle="-", color=col, lw=0.7), va="center")
ax2.set_title("换 σ：越大越矮越宽，曲线下面积始终为 1")
ax2.set_xlabel("x")
ax2.legend(loc="upper left", fontsize=9)
ax1.set_xlim(-7, 7)
ax2.set_xlim(-7, 7)
save_jpeg(fig, NOTE, "mu-sigma-shapes")

print({k: round(float(v), 6) for k, v in probs.items()})
