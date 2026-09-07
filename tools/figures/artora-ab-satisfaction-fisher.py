"""notes/case/artora-ab-satisfaction-fisher.md 的图。数据：09-08 00:00 读数（对照 185/307，试验 191/277）。"""
import sys
from math import sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

A_S, A_N = 185, 307   # 对照
B_S, B_N = 191, 277   # 试验
Z = 1.959964


def wilson(s, n, z=Z):
    p = s / n
    c = p + z * z / (2 * n)
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    den = 1 + z * z / n
    return (c - h) / den, (c + h) / den


pa, pb = A_S / A_N, B_S / B_N
la, ua = wilson(A_S, A_N)
lb, ub = wilson(B_S, B_N)
d = pb - pa
# Newcombe（score）法：两比例差的区间
lo = d - sqrt((pb - lb) ** 2 + (ua - pa) ** 2)
hi = d + sqrt((ub - pb) ** 2 + (pa - la) ** 2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw=dict(width_ratios=[1.1, 1]))
# 左：两组满意度 + Wilson 95% CI
xs = [0, 1]
ax1.bar(xs, [pa * 100, pb * 100], color=[C_A, C_B], width=0.55)
ax1.errorbar(xs, [pa * 100, pb * 100],
             yerr=[[(pa - la) * 100, (pb - lb) * 100], [(ua - pa) * 100, (ub - pb) * 100]],
             fmt="none", ecolor="black", capsize=6, lw=1.4)
ax1.set_xticks(xs, [f"对照 a\n满意 {A_S} / 提交 {A_N}", f"试验 b\n满意 {B_S} / 提交 {B_N}"])
for x, p_, l, u in zip(xs, (pa, pb), (la, lb), (ua, ub)):
    ax1.text(x, u * 100 + 1.2, f"{p_*100:.2f}%\n[{l*100:.1f}, {u*100:.1f}]", ha="center", va="bottom", fontsize=10)
ax1.set_ylim(0, 90)
ax1.set_ylabel("满意度 %")
ax1.set_title("两组满意度（误差线 = Wilson 95% CI）")
# 右：差值与 Newcombe CI
ax2.errorbar([d * 100], [0], xerr=[[(d - lo) * 100], [(hi - d) * 100]], fmt="o", color=C_HI, capsize=8, lw=2, ms=8)
ax2.axvline(0, color=C_GRAY, ls="--", lw=1)
ax2.set_yticks([])
ax2.set_ylim(-1, 1)
ax2.set_xlim(-4, 20)
ax2.set_xlabel("Δ = 试验 − 对照（百分点）")
ax2.set_title("差值与 95% 置信区间（Newcombe）")
ax2.text(d * 100, 0.14, f"Δ = +{d*100:.2f}pp", ha="center", va="bottom", color=C_HI, fontsize=12)
ax2.text(lo * 100, -0.16, f"{lo*100:+.1f}", ha="center", va="top", fontsize=10)
ax2.text(hi * 100, -0.16, f"{hi*100:+.1f}", ha="center", va="top", fontsize=10)
ax2.text(0.98, 0.04, "区间不含 0 ⇔ 双侧检验在 α=0.05 下显著\nFisher 双侧 p = 0.031", transform=ax2.transAxes,
         ha="right", va="bottom", fontsize=9.5, bbox=dict(boxstyle="round", fc="white", ec=C_GRAY))
fig.suptitle("Artora 识别满意度 A/B · 09-08 00:00 读数", y=1.02)
save_jpeg(fig, "artora-ab-satisfaction-fisher", "ci")
print(f"Δ={d*100:.2f}pp  Newcombe CI=[{lo*100:.2f}, {hi*100:.2f}]  Wilson a=[{la*100:.2f},{ua*100:.2f}] b=[{lb*100:.2f},{ub*100:.2f}]")

# ---- 图 2：如果重来，样本量该定多少：两比例检验的正态近似公式，基线 60.26%，α=0.05 双侧，功效 80% ----
from math import ceil  # noqa: E402
Z_A, Z_B = 1.959964, 0.841621   # α/2 = 0.025 与功效 0.8 对应的正态分位数
base = A_S / A_N
deltas = [d_ / 1000 for d_ in range(20, 151)]      # 2pp ~ 15pp


def n_per_arm(p0, delta, za=Z_A, zb=Z_B):
    p1 = p0 + delta
    return (za * sqrt(2 * (p0 + p1) / 2 * (1 - (p0 + p1) / 2)) + zb * sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2 / delta ** 2


ns = [n_per_arm(base, d_) for d_ in deltas]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
ax.plot([d_ * 100 for d_ in deltas], ns, color=C_A, lw=2)
obs_d = B_S / B_N - A_S / A_N
n_obs = n_per_arm(base, obs_d)
ax.axvline(obs_d * 100, color=C_HI, ls="--", lw=1)
ax.axhline(n_obs, color=C_HI, ls="--", lw=1)
ax.plot([obs_d * 100], [n_obs], "o", color=C_HI, ms=7)
ax.annotate(f"本次观测到的差 {obs_d*100:.2f}pp\n→ 每组约 {ceil(n_obs)} 人才有 80% 功效",
            xy=(obs_d * 100, n_obs), xytext=(obs_d * 100 + 1.2, n_obs + 900),
            arrowprops=dict(arrowstyle="->", color=C_HI), color=C_HI, fontsize=10)
ax.axhline(A_N, color=C_GRAY, ls=":", lw=1)
ax.text(14.8, A_N + 60, f"09-08 读数时对照组 n = {A_N}", ha="right", color=C_GRAY, fontsize=9.5)
ax.set_yscale("log")
ax.set_ylim(80, 20000)
ax.set_xlabel("要检出的真实满意率差 Δ（百分点），基线 60.26%")
ax.set_ylabel("每组需要的提交数（对数轴）")
ax.set_title("检出多大的差，需要多少样本（α = 0.05 双侧，功效 80%）")
save_jpeg(fig, "artora-ab-satisfaction-fisher", "sample-size")
print(f"n per arm to detect {obs_d*100:.2f}pp at 80% power: {n_obs:.1f}; for 5pp: {n_per_arm(base, 0.05):.0f}; for 3pp: {n_per_arm(base, 0.03):.0f}")
