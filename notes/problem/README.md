# problem/：一道题一篇

**放什么**：有题面、有输入输出的题。力扣、Codeforces、牛客、系统设计题。

**不放什么**：解题套路的通用讲解。那是 `../pattern/`，这里用 `patterns` 指过去。

## id 命名

`<平台缩写>-<四位题号>-<slug>`：`lc-0003-longest-substring-without-repeating`。没有题号的用 `sd-<slug>`（系统设计）或 `misc-<slug>`。题号补零到四位，排序才对。

## 正文结构（必需标题，lint 会查）

```markdown
## 题意
一两句话复述题目，不贴原题全文（有 url 字段）。列清输入输出和关键约束。

## 思路
先说怎么想到的（识别出是什么套路、卡在哪、怎么突破），再说算法。这是复习时最有用的一节，别只写「用滑动窗口」。

## 代码
一个语言一个代码块，标清语言。要能直接跑。

## 复杂度
时间、空间，一行。

## 变体（可选）
这题的变体、追问、和相近题的区别。
```

## 字段

| 字段 | 说明 |
|---|---|
| `platform` | 必填：`leetcode` / `codeforces` / `nowcoder` / `other` |
| `number` | 题号，字符串 |
| `difficulty` | 必填：`easy` / `medium` / `hard` |
| `url` | 题目链接 |
| `patterns` | 用到的 pattern id，可多个 |
| `related` | 相近题 |
| `tags` | 至少一个 `leetcode` 或 `algorithm`，加数据结构标签如 `data-structure` |

## 与 pattern 的关系

做完题发现「这套路我第二次遇到了」，去 `../pattern/` 建一篇，把两道题的 `patterns` 都指过去。`maps/leetcode.md` 按 pattern 归组，题单自然就出来了。
