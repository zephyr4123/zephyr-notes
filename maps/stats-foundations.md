---
id: stats-foundations
type: map
title: 概率与统计基础
summary: 从分布到检验的阅读顺序：先概率论（分布与极限定理），再统计推断框架，再具体检验，最后看它们在业务里怎么落地。
updated: 2026-09-08
---

# 概率与统计基础

<!-- 索引页：每一行都必须是链接。这是一条学习路径，按顺序读；后面的每篇都只依赖前面的 -->

## 第一层：随机变量与分布（概率论）
- [二项分布](../notes/concept/probability/binomial-distribution.md) ← 一切的起点：n 次独立试验里成功几次；期望、方差、偏度都从这里推
- [超几何分布](../notes/concept/probability/hypergeometric-distribution.md) ← 二项的"不放回"版本；两个二项条件在总和上会变成它，这是 Fisher 检验的核心
- [正态分布](../notes/concept/probability/normal-distribution.md) ← 密度公式每个部件从哪来、归一化常数怎么算、为什么只需要一张 N(0,1) 表
- [卡方分布](../notes/concept/probability/chi-square-distribution.md) ← 标准正态平方和；k=1 密度从换元推出，可加性从 MGF 推出

## 第二层：极限定理（概率论）
- [中心极限定理](../notes/concept/probability/central-limit-theorem.md) ← 为什么平均总是近似正态；MGF 证明思路；收敛快慢决定了"期望频数至少 5"这条规则

## 第三层：统计推断的框架（统计学）
- [假设检验与 p 值](../notes/concept/statistics/hypothesis-testing.md) ← 所有检验共用的逻辑：H0、零分布、p 值是什么不是什么、两类错误、功效与样本量、常见误用

## 第四层：具体检验（统计学）
- [z 检验：单比例与两比例](../notes/concept/statistics/z-test.md) ← 由 CLT 直接得到；Wald 与 Wilson 区间从这里反解出来
- [卡方检验（列联表独立性）](../notes/concept/statistics/chi-square-test.md) ← 二乘二表上它就是 z 的平方；统计量为什么长那样
- [Fisher 精确检验](../notes/concept/statistics/fisher-exact-test.md) ← 条件在总成功数上消掉未知参数，超几何分布直接算精确 p

## 第五层：落地
- [Artora 识别优化 A/B：小流量下用 Fisher 判显著](../notes/case/artora-ab-satisfaction-fisher.md) ← 以上全部在一个真实实验里怎么用、怎么复盘
- [业务 × 原理](math-in-biz.md) ← 按原理找落地案例的索引

## 未归类
