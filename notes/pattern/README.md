# pattern/：反复出现的套路

**放什么**：在 ≥ 2 篇 `problem` 或 `case` 里重复出现的做法。滑动窗口、双指针、分布式锁、小样本显著性检验。

**门槛**：出现过两次再写。只出现一次的「套路」大概率只是那道题的解法，留在 problem 里。

## 正文结构（必需标题，lint 会查）

```markdown
## 识别信号
看到什么特征就该想到它。「连续子数组 + 最值」→ 滑动窗口。「样本 < 30 且二分类」→ Fisher。这一节决定你能不能在新问题上认出它。

## 模板
可以直接套的骨架代码或步骤清单。

## 例子
链向用了它的 problem / case，一行一个，说清每个例子体现的是哪个变化点。

## 边界（可选）
什么时候看着像但不该用；常见错法。
```

## 字段

| 字段 | 说明 |
|---|---|
| `related` | 相近套路（滑动窗口 vs 双指针）、依赖的 concept |
| `tags` | `algorithm` / `system-design` 等领域标签 |

不需要字段列「哪些题用了我」，problem 的 `patterns` 和 case 的 `uses` 指过来，反链就是题单。

## id 命名

套路名本身：`sliding-window`、`two-pointers`、`distributed-lock`、`small-sample-significance`。
