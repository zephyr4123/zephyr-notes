"""notes/concept/probability/binomial-distribution.md 的图。

四张图都从 pmf 直接算，不用随机模拟：
  pmf-grid     不同 (n, p) 下的 pmf，标出均值与 ±1 标准差，看形状随参数怎么变
  skewness     偏度 (1-2p)/sqrt(np(1-p)) 随 n 与随 np 的衰减，几条不同 p
  neighbors    左：有放回（二项）vs 无放回（超几何，总体越大越接近）；右：n 大 p 小时二项 ≈ 泊松，正态套不上
  tail         n=277, p=0.356 下 P(X ≤ 86) 的精确面积与正态近似
末尾把正文用到的数字全部打印出来，笔记里的每个数都能在这里对上。
"""
import sys
from math import sqrt
from pathlib import Path

import numpy as np
from scipy.stats import binom, hypergeom, norm, poisson

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

NOTE = "binomial-distribution"


def skew(n, p):
    return (1 - 2 * p) / sqrt(n * p * (1 - p))


# ---- 图 1：pmf 网格 ----
ns = [5, 20, 100]
ps = [0.1, 0.356, 0.5]
fig, axes = plt.subplots(len(ns), len(ps), figsize=(11, 8.2))
for i, n in enumerate(ns):
    for j, p in enumerate(ps):
        ax = axes[i][j]
        mu, sd = n * p, sqrt(n * p * (1 - p))
        ks = np.arange(0, n + 1)
        pm = binom.pmf(ks, n, p)
        ax.bar(ks, pm, width=0.85, color=C_A, alpha=0.8)
        ax.axvspan(mu - sd, mu + sd, color=C_B, alpha=0.18, lw=0)
        ax.axvline(mu, color=C_HI, lw=1.6)
        lo = max(-0.6, mu - 4 * sd - 0.5) if n > 5 else -0.6
        hi = min(n + 0.6, mu + 4 * sd + 0.5) if n > 5 else n + 0.6
        ax.set_xlim(lo, hi)
        ax.set_title(f"n={n}, p={p}\n均值 {mu:.1f}，标准差 {sd:.2f}，偏度 {skew(n, p):+.2f}", fontsize=10)
        if i == len(ns) - 1:
            ax.set_xlabel("成功次数 k")
        if j == 0:
            ax.set_ylabel("P(X = k)")
axes[0][0].bar([0], [0], color=C_A, alpha=0.8, label="pmf")
axes[0][0].axvline(-10, color=C_HI, lw=1.6, label="均值 np")
axes[0][0].axvspan(-11, -10, color=C_B, alpha=0.4, lw=0, label="均值 ±1 标准差")
fig.legend(*axes[0][0].get_legend_handles_labels(), loc="lower center", ncol=3, fontsize=10, frameon=False)
fig.suptitle("二项分布 pmf：p 决定歪向哪边，n 变大后柱子越来越对称、相对越来越集中", y=0.995)
fig.tight_layout(rect=(0, 0.04, 1, 0.98))
save_jpeg(fig, NOTE, "pmf-grid")

# ---- 图 2：偏度随 n 衰减 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
ns_line = np.logspace(0, 4, 300)
p_lines = [(0.5, C_GRAY), (0.356, C_A), (0.2, "#55A868"), (0.1, C_B), (0.02, C_HI)]
for p, c in p_lines:
    g = np.array([skew(n, p) for n in ns_line])
    ax1.plot(ns_line, g, color=c, lw=2, label=f"p = {p}")
    ax2.plot(ns_line * p, g, color=c, lw=2, label=f"p = {p}")
ax1.set_xscale("log"); ax2.set_xscale("log")
ax1.set_ylim(-0.05, 2.0); ax2.set_ylim(-0.05, 2.0)
ax1.axhline(0.3, color="black", lw=0.8, ls=":")
ax1.text(1.2, 0.33, "偏度 0.3", fontsize=9)
ax1.set_xlabel("试验次数 n"); ax1.set_ylabel("偏度 (1-2p)/√(np(1-p))")
ax1.set_title("固定 p，偏度按 1/√n 衰减；p 越小起点越高、要的 n 越多")
ax1.legend(loc="upper right")
xs = np.logspace(-1, 3, 200)
ax2.plot(xs, 1 / np.sqrt(xs), color="black", lw=1.2, ls="--", label="参考线 1/√(np)")
for v, ha, x_off, y_off in ((5, "right", 0.93, 1.55), (10, "left", 1.08, 1.75)):
    ax2.axvline(v, color="black", lw=0.8, ls=":")
    ax2.text(v * x_off, y_off, f"np = {v}\n偏度 ≈ {1 / sqrt(v):.2f}", fontsize=9, ha=ha)
ax2.set_xlim(0.3, 1000)
ax2.set_xlabel("期望成功数 np"); ax2.set_ylabel("偏度")
ax2.set_title("横轴换成 np：p 小时几条线并到 1/√(np) 上，管用的是期望成功数")
ax2.legend(loc="upper right")
fig.tight_layout()
save_jpeg(fig, NOTE, "skewness")

# ---- 图 3：相邻分布 ----
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))
n_draw, p_pop = 20, 0.36
ks = np.arange(0, n_draw + 1)
ax1.bar(ks, binom.pmf(ks, n_draw, p_pop), width=0.85, color=C_A, alpha=0.35, label=f"二项 Bin({n_draw}, {p_pop})：有放回")
for N, c, m in [(50, C_HI, "o"), (200, C_B, "s"), (2000, "#55A868", "^")]:
    K = round(N * p_pop)
    ax1.plot(ks, hypergeom.pmf(ks, N, K, n_draw), color=c, marker=m, ms=4.5, lw=1.2,
             label=f"超几何 N={N}, K={K}：无放回，方差 ×{(N - n_draw) / (N - 1):.2f}")
ax1.set_xlim(-0.6, 16.6)
ax1.set_ylim(0, 0.29)
ax1.set_xlabel(f"抽 {n_draw} 个里的成功数 k"); ax1.set_ylabel("概率")
ax1.set_title("无放回抽样：总体 N 越大越接近二项（有放回）")
ax1.legend(loc="upper right", fontsize=9)

n_big, p_small = 1000, 0.005
lam = n_big * p_small
ks2 = np.arange(0, 16)
ax2.bar(ks2, binom.pmf(ks2, n_big, p_small), width=0.85, color=C_A, alpha=0.8, label=f"二项 Bin({n_big}, {p_small})")
ax2.plot(ks2, poisson.pmf(ks2, lam), color=C_HI, marker="o", ms=5, lw=0, label=f"泊松 λ = np = {lam:.0f}")
xs2 = np.linspace(-1, 15, 300)
sd2 = sqrt(n_big * p_small * (1 - p_small))
ax2.plot(xs2, norm.pdf(xs2, lam, sd2), color=C_GRAY, lw=1.8, ls="--", label=f"正态 N({lam:.0f}, {sd2:.2f}²)")
ax2.set_xlim(-0.6, 15.6)
ax2.set_xlabel("成功数 k")
ax2.set_title(f"n 大 p 小：二项几乎就是泊松；正态套不上（偏度 {skew(n_big, p_small):.2f}）")
ax2.legend(loc="upper right", fontsize=9)
fig.tight_layout()
save_jpeg(fig, NOTE, "neighbors")

# ---- 图 4：最小算例里的尾概率 ----
n, p, k_obs = 277, 0.356, 86
mu, sd = n * p, sqrt(n * p * (1 - p))
ks = np.arange(60, 140)
pm = binom.pmf(ks, n, p)
fig, ax = plt.subplots(figsize=(9, 4.4))
ax.bar(ks, pm, width=0.9, color=C_A, alpha=0.45, label="Bin(277, 0.356) 的 pmf")
mask = ks <= k_obs
ax.bar(ks[mask], pm[mask], width=0.9, color=C_HI, alpha=0.9, label=f"k ≤ {k_obs} 的柱子，面积 = {binom.cdf(k_obs, n, p):.4f}")
xs = np.linspace(60, 140, 400)
ax.plot(xs, norm.pdf(xs, mu, sd), color="black", lw=1.5, ls="--", label=f"正态 N({mu:.1f}, {sd:.2f}²)")
ax.axvline(mu, color=C_HI, lw=1, ls=":")
ax.axvline(k_obs + 0.5, color="black", lw=0.8, ls=":")
ax.text(k_obs, ax.get_ylim()[1] * 0.60, f"连续性校正切在 {k_obs}.5 ", fontsize=9, ha="right")
ax.set_xlabel("成功数 k"); ax.set_ylabel("概率")
ax.set_title(f"P(X ≤ {k_obs})：精确 {binom.cdf(k_obs, n, p):.4f}，正态近似不校正 {norm.cdf((k_obs - mu) / sd):.4f}，校正后 {norm.cdf((k_obs + 0.5 - mu) / sd):.4f}")
ax.legend(loc="upper left", fontsize=9)
save_jpeg(fig, NOTE, "tail")

# ---- 正文用到的数字 ----
print("n=4, p=0.5 pmf:", [f"{v:.4f}" for v in binom.pmf(np.arange(5), 4, 0.5)])
print(f"n=277, p=0.356: mean={mu:.3f} var={n*p*(1-p):.3f} sd={sd:.4f} skew={skew(n, p):.4f}")
print(f"  P(X<=86) exact={binom.cdf(86, n, p):.4f}  normal={norm.cdf((86 - mu) / sd):.4f}  normal+cc={norm.cdf((86.5 - mu) / sd):.4f}  z={(86 - mu) / sd:.3f}")
lo, hi = int(np.ceil(mu - sd)), int(np.floor(mu + sd))
print(f"  mean±sd covers k in [{lo}, {hi}], mass={binom.cdf(hi, n, p) - binom.cdf(lo - 1, n, p):.4f}")
lo2, hi2 = int(np.ceil(mu - 2 * sd)), int(np.floor(mu + 2 * sd))
print(f"  mean±2sd covers k in [{lo2}, {hi2}], mass={binom.cdf(hi2, n, p) - binom.cdf(lo2 - 1, n, p):.4f}")
print(f"  pmf(98)={binom.pmf(98, n, p):.4f} pmf(99)={binom.pmf(99, n, p):.4f}")
print("skewness table:")
for p_ in (0.5, 0.356, 0.1, 0.01):
    print("  p=", p_, {n_: round(skew(n_, p_), 3) for n_ in (10, 100, 277, 1000)},
          f"n for |skew|<=0.3: {(1 - 2 * p_) ** 2 / (0.09 * p_ * (1 - p_)):.1f}")
print(f"skew at np=5 (p->0): {1/sqrt(5):.3f}, np=10: {1/sqrt(10):.3f}")
# 偏度改写成 a=np, b=n(1-p) 的函数后，在 a,b>=5 / >=10 的网格上扫上确界，应逼近 1/sqrt(a_min)
_gam = lambda a, b: np.abs(b - a) / np.sqrt((a + b) * a * b)
for a_min in (5, 10):
    grid = np.logspace(np.log10(a_min), 6, 400)
    A, B = np.meshgrid(grid, grid)
    print(f"  sup |skew| over a,b>={a_min}: {_gam(A, B).max():.4f}  (1/sqrt({a_min})={1/sqrt(a_min):.4f})")
# 适用边界：批内共享随机 P ~ Beta(3,6)、m=5 时的全方差公式核对
_al, _be, _m = 3, 6, 5
_pbar = _al / (_al + _be)
_vp = _al * _be / ((_al + _be) ** 2 * (_al + _be + 1))
_rng = np.random.default_rng(0)
_X = _rng.binomial(_m, _rng.beta(_al, _be, 2_000_000))
print(f"shared P~Beta(3,6), m=5: formula var={_m*_pbar*(1-_pbar)+_m*(_m-1)*_vp:.4f} "
      f"binomial var={_m*_pbar*(1-_pbar):.4f} rho={_vp/(_pbar*(1-_pbar)):.4f} simulated var={_X.var():.4f}")
print("hypergeom variance factors:", {N: round((N - 20) / (N - 1), 3) for N in (50, 200, 2000)})
print(f"Bin(1000,0.005) vs Poisson(5) max |diff| = {np.max(np.abs(binom.pmf(ks2, 1000, 0.005) - poisson.pmf(ks2, 5))):.5f}")
