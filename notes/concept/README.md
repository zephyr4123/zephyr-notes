# concept/：原理、定义、推导

**放什么**：换任何业务场景都成立的内容。一个原理一篇。Fisher 精确检验、CAP 定理、幂等性、贝叶斯定理。

**不放什么**：具体业务的数据、参数、踩坑。那些进 `../case/`，用 `uses` 指回这里。写着写着出现「我们的 AB 实验」「某某系统」这种词，就是该剪去 case 的信号。

## 正文结构（必需标题，lint 会查）

```markdown
## 解决什么问题
一段话：什么类型的场景会遇到这个问题。用抽象描述（「2×2 列联表、小样本」），不用业务描述（「新按钮点击率」）。

## 原理
推导 / 定义 / 直觉解释。这是笔记的主体。公式用 $...$，能给直觉就给直觉。

## 适用边界
什么时候用它、什么时候不该用、和相近方法的区别（Fisher vs 卡方）。面试和实战最常问的就是这一节。

## 最小算例（可选）
一个最小的数字例子或几行代码，能跑通那种。
```

## 字段

| 字段 | 说明 |
|---|---|
| `aliases` | 别名，中英文都列：`[费舍尔精确检验, Fisher's exact test]`。搜索和 Chatbot 召回靠它 |
| `related` | 相近/对比的其他 concept：`[chi-square-test]` |

不需要列「谁用了我」。反向关系看反链。

## 判断是否该新建

先 `ls notes/concept/` 看有没有相近的。同一个原理的不同侧面（比如「贝叶斯定理」和「朴素贝叶斯分类器」）是两篇，用 `related` 连；同一个原理的不同讲法是一篇，补充进去。

## 例

```yaml
---
id: fisher-exact-test
type: concept
title: Fisher 精确检验
summary: 2×2 列联表小样本下计算精确 p 值的方法，期望频数不足时替代卡方检验。
tags: [statistics, hypothesis-testing]
aliases: [费舍尔精确检验, Fisher's exact test]
related: [chi-square-test]
status: stable
created: 2026-09-07
updated: 2026-09-07
---
```
