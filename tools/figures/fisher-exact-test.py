"""notes/concept/fisher-exact-test.md 的图。数据：Artora 09-08 00:00 读数（试验 191/277，对照 185/307）。"""
import sys
from math import comb, erf, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

# 2×2 表：试验放第一行
A_S, A_N = 191, 277      # 试验 满意 / 提交
C_S, C_N = 185, 307      # 对照 满意 / 提交


def hyper_pmf(r1, c1, n):
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return {x: comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1) for x in range(lo, hi + 1)}


def fisher_two_sided(a, b, c, d):
    n, r1, c1 = a + b + c + d, a + b, a + c
    pmf = hyper_pmf(r1, c1, n)
    p0 = pmf[a]
    return sum(v for v in pmf.values() if v <= p0 * (1 + 1e-7))


def chi2_p(a, b, c, d, yates=False):
    n = a + b + c + d
    rows, cols = (a + b, c + d), (a + c, b + d)
    obs = ((a, b), (c, d))
    stat = 0.0
    for i in range(2):
        for j in range(2):
            e = rows[i] * cols[j] / n
            diff = abs(obs[i][j] - e) - (0.5 if yates else 0)
            stat += max(diff, 0) ** 2 / e
    return 2 * (1 - 0.5 * (1 + erf(sqrt(stat) / sqrt(2))))


# ---- 图 1：H0 下试验组满意数的超几何分布，标出观测值与双侧 p 的尾部 ----
n = A_N + C_N
r1, c1 = A_N, A_S + C_S
pmf = hyper_pmf(r1, c1, n)
p_obs = pmf[A_S]
xs = [x for x in pmf if pmf[x] > 1e-6]
fig, ax = plt.subplots(figsize=(9, 4.6))
for x in xs:
    tail = pmf[x] <= p_obs * (1 + 1e-7)
    ax.bar(x, pmf[x], width=0.9, color=C_HI if tail else C_A, alpha=0.95 if tail else 0.55)
exp = r1 * c1 / n
ax.axvline(exp, color=C_GRAY, ls="--", lw=1)
ax.text(exp + 0.6, max(pmf.values()) * 0.92, f"H0 期望\n{exp:.1f}", ha="left", va="top", color=C_GRAY)
ax.annotate(f"观测 a = {A_S}\nP(A=191) = {p_obs:.4f}", xy=(A_S, p_obs), xytext=(A_S + 6, p_obs * 4),
            arrowprops=dict(arrowstyle="->", color=C_HI), color=C_HI)
p2 = fisher_two_sided(A_S, A_N - A_S, C_S, C_N - C_S)
ax.set_title(f"固定边际后，H0 下「试验组满意数」的超几何分布（n={n}, r1={r1}, c1={c1}）")
ax.set_xlabel("试验组满意数 a")
ax.set_ylabel("P(A = a)")
ax.text(0.02, 0.95, f"红色柱 = 概率 ≤ P(A=191) 的所有表\n它们的和 = 双侧 p = {p2:.3f}",
        transform=ax.transAxes, va="top", bbox=dict(boxstyle="round", fc="white", ec=C_HI))
save_jpeg(fig, "fisher-exact-test", "pmf")

# ---- 图 2：等比例缩放假想表，Fisher / 卡方 / Yates 的 p 随每组样本量变化 ----
scales = [s / 100 for s in range(3, 101)]
rows = []
for s in scales:
    an, cn = max(2, round(A_N * s)), max(2, round(C_N * s))
    a_s, c_s = round(A_S / A_N * an), round(C_S / C_N * cn)
    a_s, c_s = min(max(a_s, 0), an), min(max(c_s, 0), cn)
    tbl = (a_s, an - a_s, c_s, cn - c_s)
    nn = sum(tbl)
    min_exp = min((a_s + c_s) * an, (an - a_s + cn - c_s) * an, (a_s + c_s) * cn, (an - a_s + cn - c_s) * cn) / nn
    rows.append((an + cn, fisher_two_sided(*tbl), chi2_p(*tbl), chi2_p(*tbl, yates=True), min_exp))
ns = [r[0] for r in rows]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(ns, [r[1] for r in rows], color=C_HI, lw=2, label="Fisher 精确（双侧）")
ax.plot(ns, [r[2] for r in rows], color=C_A, lw=1.6, label="卡方（无校正）")
ax.plot(ns, [r[3] for r in rows], color=C_B, lw=1.6, ls="--", label="卡方（Yates 校正）")
ax.axhline(0.05, color=C_GRAY, ls=":", lw=1)
ax.text(ns[-1], 0.052, "α = 0.05", ha="right", va="bottom", color=C_GRAY)
first_ok = next(r[0] for r in rows if r[4] >= 5)
ax.axvline(first_ok, color=C_GRAY, ls="--", lw=1)
ax.annotate(f"虚线左侧：最小期望频数 < 5\n卡方近似不可靠的区域（总样本 < {first_ok}）", xy=(first_ok, 0.62), xytext=(200, 0.8),
            color=C_GRAY, fontsize=9.5, arrowprops=dict(arrowstyle="->", color=C_GRAY))
ax.set_ylim(0, 1)
ax.set_xlabel("总提交数（两组按 Artora 实际比例等比例缩放的假想表）")
ax.set_ylabel("p 值")
ax.set_title("同样的满意率差（60.3% vs 69.0%），三种检验的 p 随样本量怎么变")
ax.legend(loc="upper right")
save_jpeg(fig, "fisher-exact-test", "vs-chi2")

# ---- 图 3：玩具表 [[3,1],[1,3]]：n=8 时分布只有 5 根柱，双侧 p 只能取 3 个值 ----
toy = hyper_pmf(4, 4, 8)
fig, ax = plt.subplots(figsize=(8, 4.2))
labels = {0: "2/70", 1: "34/70", 2: "1", 3: "34/70", 4: "2/70"}
for x, pr in toy.items():
    ax.bar(x, pr, width=0.7, color=C_HI if x in (0, 4) else C_A, alpha=0.9 if x in (0, 4) else 0.6)
    ax.text(x, pr + 0.012, f"P={round(pr * 70)}/70", ha="center", fontsize=10)
    ax.text(x, -0.06, f"双侧 p = {labels[x]}", ha="center", fontsize=9.5, color=C_HI if x in (0, 4) else "#444")
ax.axhline(0, color="black", lw=0.8)
ax.set_ylim(-0.1, 0.6)
ax.set_xticks(range(5))
ax.set_xlabel("组 1 的成功数 a")
ax.set_ylabel("H0 下的概率")
ax.set_title("n = 8、r1 = c1 = 4 时的超几何分布：只有 5 种可能的表，p 值只能取 3 个值")
ax.text(0.02, 0.95, "只有 a = 0 或 4 才能 p < 0.05\n真实第一类错误率 = 2/70 ≈ 2.9%，不是 5%",
        transform=ax.transAxes, ha="left", va="top", fontsize=10, bbox=dict(boxstyle="round", fc="white", ec=C_HI))
save_jpeg(fig, "fisher-exact-test", "toy-pmf")
