"""notes/concept/statistics/hypothesis-testing.md 的图。

四张图：
  null-distribution  零分布 + 观测值 + p 值阴影 + 拒绝域（用 Artora 的 z = 2.19）
  p-uniform          H0 下 p 值服从均匀分布 / H1 下堆在 0 附近（模拟，固定 seed）
  power              H0 与 H1 两个分布叠加，标出 α、β、功效；左图当前样本，右图 80% 功效所需样本
  peeking            反复窥探：累计假阳性率随"看的次数"上升（模拟，固定 seed）

数字全部由脚本算出并打印，笔记正文引用打印值。
"""
import sys
from math import sqrt
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

ALPHA = 0.05
Z_CRIT = norm.ppf(1 - ALPHA / 2)          # 1.960
Z_BETA = norm.ppf(0.8)                    # 0.8416，功效 80%

# ---- Artora 表（试验 191/277，对照 185/307），算出 z ----
b_s, b_n, a_s, a_n = 191, 277, 185, 307
p_b, p_a = b_s / b_n, a_s / a_n
d = p_b - p_a
pbar = (a_s + b_s) / (a_n + b_n)
se0 = sqrt(pbar * (1 - pbar) * (1 / b_n + 1 / a_n))
z_obs = d / se0
p_obs = 2 * (1 - norm.cdf(abs(z_obs)))
print(f"z_obs={z_obs:.4f} p_obs={p_obs:.4f} z_crit={Z_CRIT:.4f}")

xs = np.linspace(-4.5, 5.5, 1001)
phi = norm.pdf(xs)

# ---------------------------------------------------------------- 图 1：零分布、p 值、拒绝域
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(xs, phi, color=C_A, lw=2, label="H0 下 T 的分布：N(0, 1)")
# 拒绝域：|T| ≥ 1.96，灰色斜线
for sign in (1, -1):
    m = sign * xs >= Z_CRIT
    ax.fill_between(xs[m], phi[m], color=C_GRAY, alpha=0.35, hatch="///", edgecolor=C_GRAY, lw=0,
                    label="拒绝域：|T| ≥ 1.96，H0 下面积 = α = 0.05" if sign == 1 else None)
# p 值：|T| ≥ 2.19，红色实心
for sign in (1, -1):
    m = sign * xs >= z_obs
    ax.fill_between(xs[m], phi[m], color=C_HI, alpha=0.75,
                    label=f"p 值：|T| ≥ {z_obs:.2f} 的面积 = {p_obs:.4f}" if sign == 1 else None)
ax.axvline(z_obs, color=C_HI, lw=1.2, ls="--")
ax.axvline(-z_obs, color=C_HI, lw=1.2, ls="--")
ax.axvline(Z_CRIT, color=C_GRAY, lw=1.2, ls=":")
ax.axvline(-Z_CRIT, color=C_GRAY, lw=1.2, ls=":")
ax.annotate(f"观测值 t = {z_obs:.2f}", xy=(z_obs, 0.04), xytext=(3.4, 0.16),
            arrowprops=dict(arrowstyle="->", color=C_HI), color=C_HI, fontsize=10.5)
ax.annotate("临界值 1.96", xy=(Z_CRIT, 0.09), xytext=(2.9, 0.26),
            arrowprops=dict(arrowstyle="->", color=C_GRAY), color="#555", fontsize=10.5)
ax.text(0, 0.16, "红色面积 < 灰色面积\n⇔ p < α\n⇔ t 落在拒绝域里", ha="center", fontsize=10.5, color="#333")
ax.set_xlabel("检验统计量 T")
ax.set_ylabel("密度")
ax.set_ylim(0, 0.43)
ax.set_title("p 值是零分布上「比观测更极端」的面积；拒绝域是事先划定的、面积为 α 的两截尾巴")
ax.legend(loc="upper right", fontsize=9.5)
save_jpeg(fig, "hypothesis-testing", "null-distribution")

# ---------------------------------------------------------------- 图 2：p 值在 H0 下均匀、在 H1 下堆向 0
# 用连续数据演示：两组各 n 个 N(μ_i, 1)，检验均值差，T = (x̄1 − x̄2)/sqrt(2/n) 在 H0 下精确服从 N(0, 1)，
# 所以 p 精确均匀。H1 的均值差取 δ = 2.19·sqrt(2/n)，让 T 的中心正好是 Artora 的 z_obs，和图 3 左图对上。
rng = np.random.default_rng(20260908)
S, n_per = 20000, 300
delta_h1 = z_obs * sqrt(2 / n_per)


def two_mean_p(shift):
    x1 = rng.normal(shift, 1.0, (S, n_per)).mean(axis=1)
    x2 = rng.normal(0.0, 1.0, (S, n_per)).mean(axis=1)
    t = (x1 - x2) / sqrt(2 / n_per)
    return 2 * (1 - norm.cdf(np.abs(t)))


p_h0 = two_mean_p(0.0)
p_h1 = two_mean_p(delta_h1)
frac_h0 = (p_h0 <= ALPHA).mean()
frac_h1 = (p_h1 <= ALPHA).mean()
pow_theory = norm.cdf(z_obs - Z_CRIT)
print(f"p-uniform sim: n={n_per}/组, S={S}, delta_h1={delta_h1:.4f}(σ=1); H0 下 P(p<=0.05)={frac_h0:.4f}; "
      f"H1 下 P(p<=0.05)={frac_h1:.4f}，公式功效 Φ(z_obs − 1.96)={pow_theory:.4f}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
bins = np.linspace(0, 1, 21)
for ax, pv, frac, color, title, ty in (
    (ax1, p_h0, frac_h0, C_A, "H0 为真（两组均值相同）：p 值均匀分布", 0.13),
    (ax2, p_h1, frac_h1, C_B, f"H1 为真（T 的中心 = {z_obs:.2f}）：p 值堆在 0 附近", frac_h1 + 0.02),
):
    counts, _ = np.histogram(pv, bins=bins)
    ax.bar(bins[:-1], counts / S, width=0.05, align="edge", color=color, alpha=0.75, edgecolor="white")
    ax.bar(bins[0], (pv <= ALPHA).mean(), width=0.05, align="edge", color=C_HI, alpha=0.9)
    ax.axhline(ALPHA, color=C_GRAY, ls="--", lw=1)
    ax.text(0.07, ty, f"p ≤ 0.05 的比例 = {frac:.3f}", color=C_HI, fontsize=10.5)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("p 值")
ax1.set_ylabel("落在该区间的比例")
ax1.text(0.98, ALPHA + 0.012, "虚线 0.05：均匀分布下每格的高度", color="#555", fontsize=9.5, ha="right")
fig.suptitle(f"每组 n = {n_per}，模拟 {S} 次：α 是「H0 为真时 p ≤ α 的概率」，功效是「H1 为真时 p ≤ α 的概率」", y=1.02)
save_jpeg(fig, "hypothesis-testing", "p-uniform")

# ---------------------------------------------------------------- 图 3：α、β、功效
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
shifts = [
    (z_obs, f"当前样本：H1 下 T 的中心 = δ/SE = {z_obs:.2f}"),
    (Z_CRIT + Z_BETA, f"样本加到每组 474：中心 = {Z_CRIT + Z_BETA:.2f}"),
]
for ax, (shift, title) in zip(axes, shifts):
    f0, f1 = norm.pdf(xs), norm.pdf(xs, loc=shift)
    ax.plot(xs, f0, color=C_A, lw=2, label="H0：N(0, 1)")
    ax.plot(xs, f1, color=C_B, lw=2, label=f"H1：N({shift:.2f}, 1)")
    m_alpha_r, m_alpha_l = xs >= Z_CRIT, xs <= -Z_CRIT
    ax.fill_between(xs[m_alpha_r], f0[m_alpha_r], color=C_HI, alpha=0.6, label="α：H0 为真却拒绝")
    ax.fill_between(xs[m_alpha_l], f0[m_alpha_l], color=C_HI, alpha=0.6)
    m_beta = xs < Z_CRIT
    ax.fill_between(xs[m_beta], f1[m_beta], color=C_GRAY, alpha=0.35, hatch="\\\\", edgecolor=C_GRAY, lw=0,
                    label="β：H1 为真却没拒绝")
    m_pow = xs >= Z_CRIT
    ax.fill_between(xs[m_pow], f1[m_pow], color=C_B, alpha=0.35, label="功效 1−β：H1 为真且拒绝")
    ax.axvline(Z_CRIT, color="black", lw=1, ls=":")
    ax.axvline(-Z_CRIT, color="black", lw=1, ls=":")
    power = 1 - norm.cdf(Z_CRIT - shift)
    beta = 1 - power
    ax.text(Z_CRIT - 0.12, 0.415, "临界值 1.96", fontsize=9.5, color="#333", ha="right")
    ax.text(3.7, 0.455, f"功效 = Φ({shift:.2f} − 1.96) = {power:.2f}\nβ = {beta:.2f}", ha="center", fontsize=10.5, color="#333")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("检验统计量 T")
    ax.set_ylim(0, 0.55)
    print(f"power fig: shift={shift:.4f} power={power:.4f} beta={beta:.4f}")
axes[0].set_ylabel("密度")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=9.5, bbox_to_anchor=(0.5, -0.06), frameon=False)
fig.suptitle("H1 把 T 的分布整体右移 δ√n/σ；移得越远，落在拒绝域右边的面积（功效）越大", y=1.02)
save_jpeg(fig, "hypothesis-testing", "power")

# ---------------------------------------------------------------- 图 4：反复窥探


def two_prop_p(x1, x2, n1, n2):
    """两比例 z 检验的双侧 p（向量化）。"""
    ph1, ph2 = x1 / n1, x2 / n2
    pb = (x1 + x2) / (n1 + n2)
    se = np.sqrt(pb * (1 - pb) * (1 / n1 + 1 / n2))
    with np.errstate(divide="ignore", invalid="ignore"):
        zz = np.where(se > 0, (ph1 - ph2) / se, 0.0)
    return 2 * (1 - norm.cdf(np.abs(zz)))


rng = np.random.default_rng(20260908)
S, K, m_per, pi0 = 20000, 30, 100, 0.6      # 每次看之前每组各新增 100 人，最多看 30 次
inc1 = rng.binomial(m_per, pi0, (S, K))
inc2 = rng.binomial(m_per, pi0, (S, K))
c1, c2 = inc1.cumsum(axis=1), inc2.cumsum(axis=1)
n_cum = m_per * np.arange(1, K + 1)
pv = two_prop_p(c1, c2, n_cum, n_cum)            # (S, K)：第 k 次看时的 p
rej = pv <= ALPHA
ever = np.maximum.accumulate(rej, axis=1)         # 前 k 次里有没有任何一次 p ≤ α
fpr = ever.mean(axis=0)
indep = 1 - (1 - ALPHA) ** np.arange(1, K + 1)
print("peeking sim: 每次每组 +100，S=20000；累计假阳性率 " + ", ".join(f"k={k}:{fpr[k - 1]:.3f}" for k in (1, 2, 3, 5, 10, 20, 30)))
print("independent 1-(1-a)^k: " + ", ".join(f"k={k}:{indep[k - 1]:.3f}" for k in (1, 2, 3, 5, 10, 20, 30)))

fig, ax = plt.subplots(figsize=(9, 4.6))
ks = np.arange(1, K + 1)
ax.plot(ks, indep, color=C_GRAY, lw=1.5, ls="--", label="若 k 次检验相互独立：1 − (1 − α)^k")
ax.plot(ks, fpr, color=C_HI, lw=2.2, marker="o", ms=4, label="反复窥探（模拟）：前 k 次里至少一次 p ≤ 0.05")
ax.axhline(ALPHA, color=C_A, lw=1.5, label="只看一次：α = 0.05")
for k in (1, 5, 10, 20, 30):
    ax.annotate(f"{fpr[k - 1]:.2f}", xy=(k, fpr[k - 1]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=10, color=C_HI)
ax.set_xlabel("看结果的次数 k（每次看之前每组各新增 100 人）")
ax.set_ylabel("H0 为真时「至少宣布过一次显著」的概率")
ax.set_ylim(0, 0.85)
ax.set_xlim(0, K + 1)
ax.set_title("H0 为真、每次 p < 0.05 就停：看得越多，假阳性率离 5% 越远")
ax.legend(loc="upper left", fontsize=9.5)
save_jpeg(fig, "hypothesis-testing", "peeking")
