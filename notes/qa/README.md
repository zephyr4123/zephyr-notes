# qa/：一问一答

**放什么**：面试八股、准备背的问答。一问一篇。「MySQL 索引为什么用 B+ 树」「TCP 三次握手为什么不是两次」。

**不放什么**：完整的原理推导。答案里需要原理就链去 `../concept/`。qa 是「怎么答」，concept 是「是什么」。

## 正文结构（必需标题，lint 会查）

```markdown
## 一句话回答
30 秒内能说完的版本。面试第一句话。

## 展开
2-3 分钟的版本：要点、为什么、对比。引用原理用链接。

## 追问（可选）
面试官常接着问什么，怎么答。
```

## 字段

| 字段 | 说明 |
|---|---|
| `difficulty` | `easy` / `medium` / `hard`，按被问到时的难度 |
| `last_reviewed` | 上次复习日期。以后做间隔复习的依据 |
| `related` | 相关 concept、相近的 qa、能佐证的 case |
| `tags` | `interview` + 领域标签（`database` / `network` / `os`） |

## id 命名

`<主题>-<问点>`：`mysql-index-btree`、`tcp-three-way-handshake`。看 id 就知道问的是什么。

## 和 concept 怎么分

同一个东西可以同时有 concept 和 qa：concept 是完整的原理，qa 是面试口径。qa 的 `related` 指向 concept。只有 qa 没有 concept 也行，别为了对称硬写。
