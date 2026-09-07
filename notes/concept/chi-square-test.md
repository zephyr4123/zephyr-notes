---
id: chi-square-test
type: concept
title: 卡方检验（列联表独立性）
summary: 用「观测值偏离独立假设下期望值的程度」判断两组比例是否相同的近似检验；每个格子期望频数都够大时和 Fisher 精确检验结论一致，格子稀疏时近似失效。
tags: [statistics, hypothesis-testing, ab-test]
aliases: [Pearson 卡方检验, chi-square test, chi-squared test, 列联表独立性检验]
related: [fisher-exact-test]
status: stable
created: 2026-09-08
updated: 2026-09-08
---

# 卡方检验（列联表独立性）

## 解决什么问题

和 [Fisher 精确检验](fisher-exact-test.md)同一个问题：一张列联表，行是分组、列是结果，问"分组和结果有没有关系"，对 $2\times 2$ 表就是"两组的成功率是否相同"。它是这类问题的默认工具，样本够大时又快又准；它的短板只在格子太稀疏的时候。

## 原理

三步：

**1. 算"如果没关系，每个格子该有多少人"。** 在 $H_0$（独立）下，格子 $(i,j)$ 的期望频数是行合计乘以列合计再除以总数：

$$
E_{ij}=\frac{r_i\,c_j}{n}
$$

**2. 算观测偏离期望多远。** 每个格子算 $(O-E)^2/E$，全部加起来：

$$
\chi^2=\sum_{i,j}\frac{(O_{ij}-E_{ij})^2}{E_{ij}}
$$

除以 $E$ 是为了把"差 10 个人"放在各自的尺度上看：期望 100 的格子差 10 是小事，期望 5 的格子差 10 是大事。对 $2\times 2$ 表有个闭式：

$$
\chi^2=\frac{n\,(ad-bc)^2}{r_1\,r_2\,c_1\,c_2}
$$

下面是 [Artora A/B](../case/artora-ab-satisfaction-fisher.md)那张表的四个格子。观测和期望的差都不大，但四个格子同向偏离（试验组满意偏多、非满意偏少，对照组反之），加起来 $\chi^2=4.80$：

![Artora 表四个格子的观测值与期望值](../../assets/chi-square-test/observed-expected.jpg)

**3. 查这个偏离有多罕见。** $H_0$ 下 $\chi^2$ 近似服从自由度 $(r-1)(c-1)$ 的卡方分布，$2\times 2$ 表就是 $\chi^2_{(1)}$：

$$
p=P\big(\chi^2_{(1)}\ge\chi^2_{\text{obs}}\big)=\operatorname{erfc}\!\left(\sqrt{\chi^2_{\text{obs}}/2}\right)
$$

Python 里一行：`erfc(sqrt(chi2 / 2))`。Artora 表：$\chi^2=4.798$，$p=0.0285$。

$2\times 2$ 表的卡方检验和"两比例 $z$ 检验"是同一个东西：$z^2=\chi^2$。Artora 表 $z=2.190$，$z^2=4.80$。

**为什么说它是近似。** 每个格子的人数本质上是二项分布（或固定边际后的超几何分布），是离散的。当期望人数够大时，这个离散分布的形状接近正态，标准化后平方求和就接近卡方分布。期望人数小时，离散分布是几根稀疏的柱子，正态曲线套不上，算出来的 $p$ 就不准：

![二项分布与正态近似：期望 99 时贴合，期望 2 时失真](../../assets/chi-square-test/approximation.jpg)

左图是 Artora 试验组"非满意"格子的实际参数（$n=277$，比例 $0.356$，期望约 $99$），近似几乎完美；右图是假想的稀疏格子（期望 $2$），差得远。这就是"期望频数 $\ge 5$"这条经验规则的来历。

**Yates 连续性校正。** 把每格的 $|O-E|$ 先减 $0.5$ 再平方，是为了补偿"用连续分布近似离散分布"。它让 $p$ 变大、检验更保守，在 Artora 表上 $\chi^2$ 从 $4.80$ 降到 $4.43$，$p$ 从 $0.0285$ 变成 $0.0354$。现代观点认为它校正过头；期望频数够大时不需要，不够大时直接换 Fisher 或无条件精确检验更合理。

## 适用边界

- **看期望频数，不看总人数。** 经验规则：所有格子 $E\ge 5$（宽松版：没有 $E<1$，且 $E<5$ 的格子不超过 $20\%$）。总人数大但结果稀有（比如投诉率 $2\%$），稀有那一列照样会不满足。**先算 $E$ 再决定用不用**，Artora 那次的教训就在这里：$n=584$ 看着不大，最小 $E$ 却有 $98.7$。
- **不满足就换精确方法**：$2\times 2$ 用 [Fisher](fisher-exact-test.md)，或功效更高的 Barnard / Boschloo；大表用 Fisher–Freeman–Halton。
- **前提是观测独立。** 同一用户多次提交、同一设备重复曝光都会破坏它。配对数据（同一批人前后测）用 McNemar。
- **只回答"有没有关系"，不回答"关系多强"。** $n$ 很大时芝麻大的差异也显著，汇报要带效应量：$2\times 2$ 报比例差和置信区间，大表报 Cramér's V。
- **同族替代**：G 检验（似然比卡方）在大样本下与 Pearson 卡方等价，稀疏时表现略有差异；有序类别用趋势检验（Cochran–Armitage），不要退化成普通卡方。

## 最小算例

零依赖实现，$2\times 2$ 专用：

```python
from math import erfc, sqrt

def chi2_2x2(a, b, c, d, yates=False):
    """表 [[a, b], [c, d]]。返回 (χ², p, 最小期望频数)。"""
    n = a + b + c + d
    rows, cols = (a + b, c + d), (a + c, b + d)
    obs = ((a, b), (c, d))
    stat, min_e = 0.0, float("inf")
    for i in range(2):
        for j in range(2):
            e = rows[i] * cols[j] / n
            min_e = min(min_e, e)
            diff = abs(obs[i][j] - e) - (0.5 if yates else 0.0)
            stat += max(diff, 0.0) ** 2 / e
    return stat, erfc(sqrt(stat / 2)), min_e
```

```python
>>> chi2_2x2(191, 86, 185, 122)            # Artora 表：试验 / 对照
(4.798..., 0.0285, 98.657...)
>>> chi2_2x2(191, 86, 185, 122, yates=True)
(4.426..., 0.0354, 98.657...)
```

有 scipy 就直接 `scipy.stats.chi2_contingency([[191, 86], [185, 122]], correction=False)`，返回值里带期望频数矩阵，顺手就能查经验规则。图由 `tools/figures/chi-square-test.py` 生成。
