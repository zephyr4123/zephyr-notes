"""notes/concept/probability/chi-square-distribution.md 的图。

四张图都由理论密度（scipy.stats.chi2 / norm）或固定 seed 的模拟生成：
  density.jpg        自由度 k=1,2,3,5,10 的密度：形状怎么随 k 变
  simulation.jpg     模拟 k 个标准正态的平方和，直方图对上理论密度（k=1 在 0 处发散、k=2 是指数分布）
  tail.jpg           同一个 p：N(0,1) 的双尾 = chi2(1) 的单尾，x=4.798
  normal-approx.jpg  k=5 与 k=30 分别叠 N(k, 2k)：近似在哪失效
"""
import sys
from math import sqrt
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

NOTE = "chi-square-distribution"
PALETTE = [C_HI, C_B, "#55A868", C_A, "#8172B2"]

# ---- 图 1：密度随自由度变化 ----
fig, ax = plt.subplots(figsize=(9, 4.8))
xs = np.linspace(0.005, 25, 2000)
for k, color in zip((1, 2, 3, 5, 10), PALETTE):
    ax.plot(xs, stats.chi2.pdf(xs, k), color=color, lw=2, label=f"k = {k}（均值 {k}，方差 {2*k}）")
    if k >= 3:  # 众数 k-2，标出来
        ax.plot([k - 2], [stats.chi2.pdf(k - 2, k)], "o", color=color, ms=5)
ax.annotate("k=1：密度在 0 处发散\n（x^(-1/2) 因子）", xy=(0.12, 1.05), xytext=(2.6, 1.02),
            fontsize=9.5, arrowprops=dict(arrowstyle="->", color=C_GRAY), color="#333")
ax.annotate("k=2：从 1/2 出发的指数衰减", xy=(0.05, 0.49), xytext=(4.5, 0.62),
            fontsize=9.5, arrowprops=dict(arrowstyle="->", color=C_GRAY), color="#333")
ax.annotate("圆点：众数 x = k − 2（k ≥ 3）", xy=(8, stats.chi2.pdf(8, 10)), xytext=(11.5, 0.22),
            fontsize=9.5, arrowprops=dict(arrowstyle="->", color=C_GRAY), color="#333")
ax.set_xlim(0, 25)
ax.set_ylim(0, 1.15)
ax.set_xlabel("x")
ax.set_ylabel("密度 f(x)")
ax.set_title("卡方分布的密度：自由度 k 越大，峰越靠右、越对称、越像正态")
ax.legend(loc="upper right")
save_jpeg(fig, NOTE, "density")

# ---- 图 2：模拟 k 个标准正态的平方和，对上理论密度 ----
rng = np.random.default_rng(20260908)
N = 200_000
Z = rng.standard_normal((N, 3))
fig, axes = plt.subplots(1, 3, figsize=(12, 3.9))
titles = ["k = 1：Z₁²", "k = 2：Z₁² + Z₂²", "k = 3：Z₁² + Z₂² + Z₃²"]
for k, ax, title in zip((1, 2, 3), axes, titles):
    s = (Z[:, :k] ** 2).sum(axis=1)
    hi = 12
    ax.hist(s[s < hi], bins=120, range=(0, hi), density=True, color=C_A, alpha=0.55,
            label=f"模拟 {N:,} 次的直方图")
    xg = np.linspace(0.01, hi, 1500)
    ax.plot(xg, stats.chi2.pdf(xg, k), color=C_HI, lw=2, label="理论密度 chi2(k)")
    ax.set_title(f"{title}\n模拟均值 {s.mean():.3f}，方差 {s.var():.3f}（理论 {k}，{2*k}）", fontsize=10.5)
    ax.set_xlabel("平方和的值")
    ax.set_xlim(0, hi)
axes[0].set_ylim(0, 1.3)
axes[0].set_ylabel("密度")
axes[0].text(1.6, 1.05, "越靠近 0 越密\n（0 附近的 Z 被平方压扁）", fontsize=9, color="#333")
axes[1].text(3.2, 0.36, "指数分布 ½·e^(−x/2)：\n从 1/2 起单调衰减，均值 2", fontsize=9, color="#333")
axes[2].text(5.2, 0.17, "峰在 x = 1（众数 k − 2）", fontsize=9, color="#333")
axes[2].legend(loc="upper right", fontsize=9)
fig.suptitle("定义即模拟：抽 k 个 N(0,1) 平方相加，直方图与理论密度重合（seed 固定）", y=1.12)
save_jpeg(fig, NOTE, "simulation")

# ---- 图 3：同一个 p，两种画法 ----
x_obs = 4.798
z_obs = sqrt(x_obs)
p_obs = stats.chi2.sf(x_obs, 1)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
zs = np.linspace(-4, 4, 801)
ax1.plot(zs, stats.norm.pdf(zs), color=C_A, lw=2)
for side in (1, -1):
    m = zs * side >= z_obs
    ax1.fill_between(zs[m], stats.norm.pdf(zs[m]), color=C_HI, alpha=0.5)
    ax1.axvline(side * z_obs, color=C_HI, ls="--", lw=1)
ax1.text(z_obs + 0.15, 0.12, f"z = {z_obs:.3f}", color=C_HI, fontsize=10)
ax1.text(-z_obs - 0.15, 0.12, f"z = −{z_obs:.3f}", color=C_HI, fontsize=10, ha="right")
ax1.set_title(f"N(0,1)：P(|Z| ≥ {z_obs:.3f}) = 双尾面积 = {p_obs:.4f}")
ax1.set_xlabel("z")
ax1.set_ylabel("密度")
cs = np.linspace(0.02, 12, 1200)
ax2.plot(cs, stats.chi2.pdf(cs, 1), color=C_A, lw=2)
m = cs >= x_obs
ax2.fill_between(cs[m], stats.chi2.pdf(cs[m], 1), color=C_HI, alpha=0.5)
ax2.axvline(x_obs, color=C_HI, ls="--", lw=1)
ax2.text(x_obs + 0.2, 0.25, f"x = {x_obs} = z²", color=C_HI, fontsize=10)
ax2.set_ylim(0, 1.2)
ax2.set_xlim(0, 12)
ax2.set_title(f"chi2(1)：P(X ≥ {x_obs}) = 单尾面积 = {p_obs:.4f}")
ax2.set_xlabel("x = z²")
fig.suptitle("X = Z² 的分布：Z 的两个尾巴被平方折到 X 的一个尾巴上，面积相同", y=1.02)
save_jpeg(fig, NOTE, "tail")

# ---- 图 4：正态近似 N(k, 2k) 在 k=5 与 k=30 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3))
for ax, k, hi in ((ax1, 5, 22), (ax2, 30, 70)):
    xg = np.linspace(-8 if k == 5 else 0, hi, 2000)
    ax.plot(xg, stats.chi2.pdf(xg, k), color=C_A, lw=2, label=f"chi2({k}) 精确")
    ax.plot(xg, stats.norm.pdf(xg, k, sqrt(2 * k)), color=C_HI, lw=2, ls="--", label=f"N({k}, {2*k}) 近似")
    q_exact = stats.chi2.ppf(0.95, k)
    q_norm = stats.norm.ppf(0.95, k, sqrt(2 * k))
    ax.axvline(q_exact, color=C_A, lw=1, ls=":")
    ax.axvline(q_norm, color=C_HI, lw=1, ls=":")
    ymax = ax.get_ylim()[1]
    ax.text(q_exact + 0.4 * (1 if k == 30 else 1), ymax * 0.55, f"95% 分位数\n精确 {q_exact:.2f}\n近似 {q_norm:.2f}",
            fontsize=9.5, color="#333")
    ax.set_xlabel("x")
    ax.set_title(f"k = {k}：偏度 √(8/k) = {sqrt(8/k):.2f}", fontsize=11.5)
    ax.legend(loc="upper left", fontsize=9.5)
neg = stats.norm.cdf(0, 5, sqrt(10))
ax1.fill_between(np.linspace(-8, 0, 200), stats.norm.pdf(np.linspace(-8, 0, 200), 5, sqrt(10)), color=C_HI, alpha=0.25)
ax1.text(-7.9, 0.072, f"近似把 {neg:.1%} 的概率\n放到了 x < 0，\n而 X 不可能为负", fontsize=9, color=C_HI)
ax1.set_ylabel("密度")
fig.suptitle("中心极限定理：k 个独立 Z² 的和，k 大了才像 N(k, 2k)；右尾是最后才像的地方", y=1.02)
save_jpeg(fig, NOTE, "normal-approx")
