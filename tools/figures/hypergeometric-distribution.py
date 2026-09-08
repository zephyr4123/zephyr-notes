"""notes/concept/probability/hypergeometric-distribution.md 的图。

图 1  同均值下超几何 vs 二项 pmf：N=20 与 N=2000 两组，看方差差异
图 2  有限总体校正因子 (N-n)/(N-1) 随抽样比例 n/N 变化
图 3  二项近似的误差随 N/n 变化（总变差距离），看「N 比 n 大 20 倍」这条经验规则
图 4  Artora 表（N=584, K=376, n=277）的超几何 pmf 与二项 pmf 对比

所有数字由 scipy.stats.hypergeom / binom 直接算，无随机模拟。
"""
import sys
from pathlib import Path

import numpy as np
from matplotlib.ticker import FuncFormatter
from scipy.stats import binom, hypergeom

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

NOTE = "hypergeometric-distribution"


def hg(N, K, n):
    """scipy 的参数名容易混：hypergeom(M=总数, n=总体里的白球数, N=抽几个)。这里统一成 (N, K, n)。"""
    return hypergeom(N, K, n)


# ---- 图 1：同均值下超几何 vs 二项，N=20 与 N=2000 ----
n, p = 10, 0.5
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
for ax, N in zip(axes, (20, 2000)):
    K = int(N * p)
    rv_h, rv_b = hg(N, K, n), binom(n, p)
    ks = np.arange(0, n + 1)
    w = 0.4
    ax.bar(ks - w / 2, rv_h.pmf(ks), w, color=C_A, label=f"超几何 N={N}, K={K}, n={n}")
    ax.bar(ks + w / 2, rv_b.pmf(ks), w, color=C_B, alpha=0.85, label=f"二项 n={n}, p={p}")
    ax.set_title(f"N={N}：sd 超几何 {rv_h.std():.2f} vs 二项 {rv_b.std():.2f}"
                 f"（校正因子 {(N - n) / (N - 1):.3f}）", fontsize=11)
    ax.set_xlabel("抽到的白球数 k")
    ax.set_xticks(ks)
    ax.set_ylim(0, 0.40)
    ax.legend(loc="upper left")
axes[0].set_ylabel("概率")
fig.suptitle("同一个均值 nK/N = 5：不放回抽样的分布更窄，N 变大后两者重合", y=1.02)
save_jpeg(fig, NOTE, "pmf-vs-binomial")

# ---- 图 2：有限总体校正因子 ----
fig, ax = plt.subplots(figsize=(8, 4.5))
f = np.linspace(0, 1, 401)
ax.plot(f, 1 - f, color=C_A, lw=2, label="方差的校正因子 (N−n)/(N−1)，N 很大时 ≈ 1 − n/N")
ax.plot(f, np.sqrt(1 - f), color=C_B, lw=2, ls="--", label="标准差的缩小比例 √((N−n)/(N−1))")
N_small = 20
ns = np.arange(1, N_small + 1)
ax.plot(ns / N_small, (N_small - ns) / (N_small - 1), "o", color=C_A, ms=4, label=f"N={N_small} 的精确值（n 取整数）")
# 标注三个点：经验规则 5%（按 N→∞ 取极限值 1−n/N）、图 1 的 N=20 例子、Artora 表
# 后两个点的纵坐标用精确校正因子 (N−n)/(N−1)，不落在近似线 1−n/N 上；N=20 时两者差 0.026，图上看得出来
pts = [
    (0.05, 0.95, "n/N = 5%，N→∞：因子 0.95", (0.04, 0.62)),
    (10 / 20, (20 - 10) / (20 - 1), f"N=20, n=10：{(20 - 10) / (20 - 1):.3f}", (0.56, 0.76)),
    (277 / 584, (584 - 277) / (584 - 1), f"Artora 表 n/N = 277/584：{(584 - 277) / 583:.3f}", (0.30, 0.30)),
]
for x, y, txt, xy in pts:
    ax.plot([x], [y], "o", color=C_HI, ms=7, zorder=5)
    ax.annotate(txt, (x, y), xytext=xy, textcoords="axes fraction", fontsize=9.5, color=C_HI,
                arrowprops=dict(arrowstyle="-", color=C_HI, lw=0.8))
ax.set_xlabel("抽样比例 n/N")
ax.set_ylabel("相对于二项分布的倍数")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1.05)
ax.set_title("有限总体校正因子：抽走的比例越大，方差比二项分布缩得越多")
ax.legend(loc="lower left", fontsize=9)
save_jpeg(fig, NOTE, "fpc")


# ---- 图 3：二项近似误差随 N/n 变化 ----
def tv_distance(N, K, n):
    ks = np.arange(0, n + 1)
    return 0.5 * np.abs(hg(N, K, n).pmf(ks) - binom(n, K / N).pmf(ks)).sum()


fig, ax = plt.subplots(figsize=(8, 4.5))
ratios = np.array([1.5, 2, 3, 4, 5, 7, 10, 15, 20, 30, 50, 100, 200, 500, 1000])
for n_, p_, color, ls in [(10, 0.5, C_A, "-"), (50, 0.5, C_B, "-"), (10, 0.2, C_A, "--")]:
    Ns = np.array([int(round(r * n_)) for r in ratios])
    Ks = np.array([int(round(p_ * N_)) for N_ in Ns])
    tv = [tv_distance(N_, K_, n_) for N_, K_ in zip(Ns, Ks)]
    ax.plot(Ns / n_, tv, marker="o", ms=4, color=color, ls=ls, label=f"n={n_}, K/N={p_}")
ax.axvline(20, color=C_HI, ls=":", lw=1.2)
ax.text(21, 0.2, "经验规则\nN ≥ 20 n\n（n/N ≤ 5%）", color=C_HI, fontsize=9.5, va="top")
ax.set_xscale("log")
ax.set_yscale("log")
plain = FuncFormatter(lambda v, _: f"{v:g}")  # 不走 mathtext，免得负号缺字形
ax.xaxis.set_major_formatter(plain)
ax.yaxis.set_major_formatter(plain)
ax.set_xlabel("N / n（总体是抽样数的几倍，对数轴）")
ax.set_ylabel("总变差距离 ½ Σ|超几何 − 二项|（对数轴）")
ax.set_title("用二项分布近似超几何的误差：大约按 1/N 下降，n 越大要求 N 也按比例变大")
ax.legend(loc="lower left")
save_jpeg(fig, NOTE, "binomial-limit")

# ---- 图 4：Artora 表 ----
N, K, n = 584, 376, 277
rv_h, rv_b = hg(N, K, n), binom(n, K / N)
ks = np.arange(150, 211)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(ks, rv_h.pmf(ks), width=0.9, color=C_A, alpha=0.85,
       label=f"超几何 N={N}, K={K}, n={n}（sd {rv_h.std():.2f}）")
ax.step(ks, rv_b.pmf(ks), where="mid", color=C_B, lw=2,
        label=f"二项 n={n}, p={K / N:.3f}（sd {rv_b.std():.2f}）")
ax.set_ylim(0, 0.085)
ax.axvline(rv_h.mean(), color=C_GRAY, ls="--", lw=1)
ax.text(rv_h.mean() + 0.6, 0.082, f"期望 nK/N = {rv_h.mean():.1f}", ha="left", va="top", color="#555", fontsize=10)
ax.axvline(191, color=C_HI, ls="--", lw=1.2)
# 注释块抬到橙色二项阶梯线之上（192–194 段高约 0.011–0.014），用箭头指回观测点
ax.annotate(f"观测 191\nP(X=191) = {rv_h.pmf(191):.4f}\n二项会给 {rv_b.pmf(191):.4f}",
            xy=(191, rv_h.pmf(191)), xytext=(196, 0.036), color=C_HI, fontsize=10, va="bottom",
            arrowprops=dict(arrowstyle="->", color=C_HI, lw=0.9))
ax.set_xlabel("试验组满意数 k")
ax.set_ylabel("概率")
ax.set_title("Artora 表：抽样比例 277/584 = 47%，二项分布比真实分布宽得多")
ax.legend(loc="upper left", fontsize=9.5)
save_jpeg(fig, NOTE, "artora")

print(f"Artora: mean={rv_h.mean():.4f} var={rv_h.var():.4f} sd={rv_h.std():.4f} "
      f"binom_sd={rv_b.std():.4f} fpc={(N - n) / (N - 1):.4f} "
      f"P(X=191)={rv_h.pmf(191):.6f} binom={rv_b.pmf(191):.6f} P(X>=191)={rv_h.sf(190):.6f}")
