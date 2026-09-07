"""notes/concept/chi-square-test.md 的图。左图数据取自 Artora 表（试验 191/277，对照 185/307）；右图是说明近似何时失效的示意。"""
import sys
from math import comb, exp, pi, sqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import C_A, C_B, C_GRAY, C_HI, plt, save_jpeg  # noqa: E402

obs = {("试验", "满意"): 191, ("试验", "非满意"): 86, ("对照", "满意"): 185, ("对照", "非满意"): 122}
rows = {"试验": 277, "对照": 307}
cols = {"满意": 376, "非满意": 208}
n = 584
exp_ = {k: rows[k[0]] * cols[k[1]] / n for k in obs}
contrib = {k: (obs[k] - exp_[k]) ** 2 / exp_[k] for k in obs}
chi2 = sum(contrib.values())

# ---- 图 1：观测 vs 期望，每格贡献 ----
keys = list(obs)
fig, ax = plt.subplots(figsize=(9, 4.6))
x = range(len(keys))
w = 0.38
ax.bar([i - w / 2 for i in x], [obs[k] for k in keys], w, color=C_A, label="观测 O")
ax.bar([i + w / 2 for i in x], [exp_[k] for k in keys], w, color=C_GRAY, alpha=0.7, label="H0 下期望 E")
for i, k in enumerate(keys):
    ax.text(i - w / 2, obs[k] + 3, f"{obs[k]}", ha="center", fontsize=10)
    ax.text(i + w / 2, exp_[k] + 3, f"{exp_[k]:.1f}", ha="center", fontsize=10, color="#555")
    ax.text(i, -22, f"(O−E)²/E = {contrib[k]:.2f}", ha="center", fontsize=9.5, color=C_HI)
ax.set_xticks(list(x), [f"{a} · {b}" for a, b in keys])
ax.set_ylim(-30, 230)
ax.set_ylabel("提交数")
ax.set_title(f"Artora 表：每个格子的观测值 vs 独立假设下的期望值，χ² = Σ(O−E)²/E = {chi2:.2f}")
ax.legend(loc="upper right")
ax.axhline(0, color="black", lw=0.8)
save_jpeg(fig, "chi-square-test", "observed-expected")


# ---- 图 2：二项分布 vs 正态近似，期望 99 与期望 2 ----
def binom_pmf(n_, p_):
    return {k: comb(n_, k) * p_ ** k * (1 - p_) ** (n_ - k) for k in range(n_ + 1)}


def normal_pdf(x_, mu, sd):
    return exp(-0.5 * ((x_ - mu) / sd) ** 2) / (sd * sqrt(2 * pi))


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, (n_, p_, title) in zip((ax1, ax2), [
    (277, 208 / 584, "试验组·非满意格子（提交−满意）：n=277, p≈0.356，期望 ≈ 99"),
    (40, 0.05, "假想稀疏格子：n=40, p=0.05，期望 = 2"),
]):
    pmf = binom_pmf(n_, p_)
    mu, sd = n_ * p_, sqrt(n_ * p_ * (1 - p_))
    ks = [k for k in pmf if pmf[k] > 1e-4]
    ax.bar(ks, [pmf[k] for k in ks], width=0.9, color=C_A, alpha=0.7, label="真实分布（二项）")
    xs_ = [ks[0] - 1 + i * (ks[-1] - ks[0] + 2) / 300 for i in range(301)]
    ax.plot(xs_, [normal_pdf(v, mu, sd) for v in xs_], color=C_HI, lw=2, label="正态近似")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("格子里的人数")
    ax.legend(loc="upper right")
ax1.set_ylabel("概率")
fig.suptitle("卡方检验靠的是「格子人数 ≈ 正态」这个近似：期望大时套得上，期望小时套不上", y=1.02)
save_jpeg(fig, "chi-square-test", "approximation")
print(f"chi2={chi2:.3f}", {f"{k[0]}·{k[1]}": round(v, 3) for k, v in contrib.items()})
