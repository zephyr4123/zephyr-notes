"""notes/concept/statistics/z-test.md 的图。

图 1：H0 下两比例之差的抽样分布（精确：两个二项分布的卷积）与正态近似，标出 Artora 观测差。
图 2：n = 30 时 Wald 与 Wilson 区间的真实覆盖率随 π 变化（按二项分布精确求和，不用模拟）；右图是 31 个可能的 x 对应的区间端点。
图 3：Wilson 区间的几何：|p̂ − π| 与 z·sqrt(π(1−π)/n) 两条曲线的交点；Wald 是把弧线换成水平线。
数据：Artora 09-08 00:00 读数（试验 191/277，对照 185/307）。
"""
import sys
from math import comb, sqrt
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

Z = stats.norm.ppf(0.975)  # 1.959964
X1, N1, X2, N2 = 191, 277, 185, 307  # 试验 / 对照


def wald(x, n, z=Z):
    p = x / n
    h = z * sqrt(p * (1 - p) / n)
    return p - h, p + h


def wilson(x, n, z=Z):
    p = x / n
    z2 = z * z
    den = 1 + z2 / n
    centre = (p + z2 / (2 * n)) / den
    half = z * sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / den
    return centre - half, centre + half


# ---- 图 1：H0 下 p̂1 − p̂2 的抽样分布 ----
p1, p2 = X1 / N1, X2 / N2
d_obs = p1 - p2
pbar = (X1 + X2) / (N1 + N2)
se0 = sqrt(pbar * (1 - pbar) * (1 / N1 + 1 / N2))
z_obs = d_obs / se0
p_two = 2 * stats.norm.sf(abs(z_obs))

# 精确分布：X1 ~ Bin(N1, pbar)，X2 ~ Bin(N2, pbar) 独立，枚举所有 (x1, x2) 组合
pmf1 = stats.binom.pmf(np.arange(N1 + 1), N1, pbar)
pmf2 = stats.binom.pmf(np.arange(N2 + 1), N2, pbar)
diffs = (np.arange(N1 + 1)[:, None] / N1 - np.arange(N2 + 1)[None, :] / N2).ravel()
probs = (pmf1[:, None] * pmf2[None, :]).ravel()
width = 0.01
edges = np.arange(-0.2, 0.2 + width, width)
hist, _ = np.histogram(diffs, bins=edges, weights=probs)
p_exact_two = probs[np.abs(diffs) >= d_obs - 1e-12].sum()

fig, ax = plt.subplots(figsize=(9, 4.6))
centers = (edges[:-1] + edges[1:]) / 2
ax.bar(centers * 100, hist / width / 100, width=width * 100 * 0.92, color=C_A, alpha=0.55,
       label="H0 下的精确分布（两个二项分布卷积，按 1pp 分箱）")
xs = np.linspace(-0.2, 0.2, 801)
pdf = stats.norm.pdf(xs, 0, se0)
ax.plot(xs * 100, pdf / 100, color=C_HI, lw=2, label=f"正态近似 N(0, {se0:.4f}²)")
right = xs >= d_obs
left = xs <= -d_obs
ax.fill_between(xs[right] * 100, pdf[right] / 100, color=C_HI, alpha=0.45)
ax.fill_between(xs[left] * 100, pdf[left] / 100, color=C_HI, alpha=0.45)
ax.axvline(d_obs * 100, color="black", ls="--", lw=1.2)
ax.axvline(-d_obs * 100, color="black", ls=":", lw=1)
ax.annotate(f"观测差 = +{d_obs*100:.2f}pp\nz = {z_obs:.3f}\n双尾面积 p = {p_two:.4f}",
            xy=(d_obs * 100, stats.norm.pdf(d_obs, 0, se0) / 100), xytext=(11.5, 0.055),
            arrowprops=dict(arrowstyle="->", color="black"), fontsize=10.5,
            bbox=dict(boxstyle="round", fc="white", ec=C_GRAY))
ax.text(-19.5, 0.092, f"精确分布里 |差| ≥ {d_obs*100:.2f}pp 的概率 = {p_exact_two:.4f}\n正态近似给的是 {p_two:.4f}，几乎一样",
        fontsize=9.5, va="top", bbox=dict(boxstyle="round", fc="white", ec=C_GRAY))
ax.set_xlim(-20, 20)
ax.set_ylim(0, 0.105)
ax.set_xlabel("p̂1 − p̂2（百分点）")
ax.set_ylabel("密度（每百分点）")
ax.set_title(f"H0：两组共用 π = {pbar:.3f} 时，试验 (n={N1}) − 对照 (n={N2}) 满意率之差的分布")
ax.legend(loc="upper right", fontsize=9)
save_jpeg(fig, "z-test", "null-distribution")
print(f"d={d_obs:.5f} se0={se0:.6f} z={z_obs:.4f} p_normal={p_two:.5f} p_exact_convolution={p_exact_two:.5f}")


# ---- 图 2：n = 30 时的真实覆盖率 + 区间端点 ----
def coverage(ci_fn, n, pi):
    return sum(comb(n, x) * pi ** x * (1 - pi) ** (n - x)
               for x in range(n + 1) if ci_fn(x, n)[0] <= pi <= ci_fn(x, n)[1])


n30 = 30
grid = np.linspace(0.005, 0.995, 991)
cov_wald = np.array([coverage(wald, n30, pi) for pi in grid])
cov_wilson = np.array([coverage(wilson, n30, pi) for pi in grid])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.22))
ax1.plot(grid, cov_wald, color=C_B, lw=1.6, label="Wald：p̂ ± z·sqrt(p̂(1−p̂)/n)")
ax1.plot(grid, cov_wilson, color=C_A, lw=1.6, label="Wilson（检验反解）")
ax1.axhline(0.95, color=C_HI, ls="--", lw=1.2, label="名义 95%")
ax1.set_ylim(0.4, 1.0)
ax1.set_xlim(0, 1)
ax1.set_xlabel("真实比例 π")
ax1.set_ylabel("P(区间盖住 π)")
ax1.set_title(f"n = {n30}：真实覆盖率随 π 变化（二项分布精确求和）", fontsize=11.5)
ax1.legend(loc="center", fontsize=9)
band = (grid >= 0.1) & (grid <= 0.9)
ax1.text(0.5, 0.45, f"π 在 [0.1, 0.9] 内的平均覆盖率：Wald {cov_wald[band].mean():.3f}，Wilson {cov_wilson[band].mean():.3f}",
         ha="center", fontsize=9, bbox=dict(boxstyle="round", fc="white", ec=C_GRAY))

xs30 = np.arange(n30 + 1)
for x in xs30:
    lw_, uw_ = wald(x, n30)
    ls_, us_ = wilson(x, n30)
    ax2.plot([x - 0.18, x - 0.18], [lw_, uw_], color=C_B, lw=2.2, solid_capstyle="butt")
    ax2.plot([x + 0.18, x + 0.18], [ls_, us_], color=C_A, lw=2.2, solid_capstyle="butt")
ax2.axhspan(1, 1.08, color=C_HI, alpha=0.12)
ax2.axhspan(-0.08, 0, color=C_HI, alpha=0.12)
ax2.axhline(0, color=C_GRAY, lw=0.8)
ax2.axhline(1, color=C_GRAY, lw=0.8)
ax2.plot([], [], color=C_B, lw=2.2, label="Wald")
ax2.plot([], [], color=C_A, lw=2.2, label="Wilson")
ax2.set_ylim(-0.08, 1.08)
ax2.set_xlim(-1, n30 + 1)
ax2.set_xlabel("观测到的成功数 x（n = 30）")
ax2.set_ylabel("95% 区间")
ax2.set_title("每个 x 对应的区间：Wald 会越出 [0, 1]", fontsize=11.5)
ax2.legend(loc="center right", fontsize=9)
ax2.text(7, -0.055, "Wald 下限 < 0（x = 1, 2, 3）", color=C_HI, fontsize=9)
ax2.text(23, 1.03, "Wald 上限 > 1（x = 27, 28, 29）", color=C_HI, fontsize=9, ha="right")
ax2.annotate("x = 0：Wald 宽度为 0", xy=(-0.18, 0.005), xytext=(0.6, 0.64), color=C_B, fontsize=9,
             arrowprops=dict(arrowstyle="->", color=C_B))
save_jpeg(fig, "z-test", "coverage")
print(f"n=30 coverage mean Wald={cov_wald.mean():.4f} Wilson={cov_wilson.mean():.4f}; band[0.1,0.9] Wald={cov_wald[band].mean():.4f} Wilson={cov_wilson[band].mean():.4f}")
for pi in (0.05, 0.1, 0.3, 0.5, 0.7):
    print(f"  pi={pi}: Wald={coverage(wald, n30, pi):.4f} Wilson={coverage(wilson, n30, pi):.4f}")


# ---- 图 3：Wilson 区间的几何 ----
def draw_geometry(ax, x, n, title):
    p = x / n
    pis = np.linspace(0.0, 1.0, 2001)
    v = np.abs(p - pis)
    arch = Z * np.sqrt(pis * (1 - pis) / n)
    flat = Z * sqrt(p * (1 - p) / n)
    lo_s, hi_s = wilson(x, n)
    lo_w, hi_w = wald(x, n)
    ax.plot(pis, v, color="black", lw=1.8, label="|p̂ − π|")
    ax.plot(pis, arch, color=C_A, lw=2, label="z·sqrt(π(1−π)/n)（H0 下的标准差）")
    ax.axhline(flat, color=C_B, lw=1.6, ls="--", label="z·sqrt(p̂(1−p̂)/n)（Wald 用 p̂ 代替 π）")
    for b in (lo_s, hi_s):
        ax.plot([b, b], [0, Z * sqrt(b * (1 - b) / n)], color=C_A, lw=1, ls=":")
        ax.plot([b], [Z * sqrt(b * (1 - b) / n)], "o", color=C_A, ms=6)
    for b in (lo_w, hi_w):
        ax.plot([b, b], [0, flat], color=C_B, lw=1, ls=":")
        ax.plot([b], [flat], "s", color=C_B, ms=5)
    ax.axvline(p, color=C_GRAY, lw=0.8)
    ax.axvline(1, color=C_HI, lw=0.8)
    ax.set_xlim(max(0, p - 0.3), min(1.05, p + 0.3) if p < 0.75 else 1.05)
    ax.set_ylim(0, flat * 2.4)
    ax.set_xlabel("候选真值 π")
    ax.set_title(title, fontsize=11)
    ax.text(p + 0.01, flat * 2.2, f"p̂ = {p:.3f}", ha="left", fontsize=9.5, color="#333")
    ax.text(0.03, 0.05, f"Wilson [{lo_s:.3f}, {hi_s:.3f}]\nWald   [{lo_w:.3f}, {hi_w:.3f}]",
            transform=ax.transAxes, va="bottom", fontsize=9.5, family="monospace",
            bbox=dict(boxstyle="round", fc="white", ec=C_GRAY))
    return lo_s, hi_s, lo_w, hi_w


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6))
r1 = draw_geometry(ax1, X1, N1, f"x = {X1}, n = {N1}：弧线几乎是平的，两种区间差不多")
r2 = draw_geometry(ax2, 27, 30, "x = 27, n = 30：弧线在 π → 1 时压向 0，Wilson 不越界，Wald 越界")
ax1.set_ylabel("距离")
handles, labels = ax1.get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.13), frameon=False)
fig.suptitle("Wilson 区间 = 所有使 |p̂ − π| ≤ z·sqrt(π(1−π)/n) 成立的 π；区间端点就是 V 形线与弧线的交点", y=1.02)
save_jpeg(fig, "z-test", "wilson-geometry")
print("geometry Artora:", [round(v, 4) for v in r1], " small:", [round(v, 4) for v in r2])
