# maps/：索引层

一个视角一个文件。**只放链接，不写正文。** 这是整个知识库唯一的硬闸：索引页一旦开始写内容，它就退化成「面试.md」这种按主题的大文件，原子笔记没人维护，结构就散了。lint 会检查每一行。

## 索引页是什么，不是什么

- 是：目录、阅读顺序、「为什么把这几篇放一起」的一句话说明。
- 不是：文章。想把几篇原子笔记合成一篇「三个场景对比」，那是内容层的一篇正常笔记，放 `notes/`，不放这里。

## 正文规则（lint 会查）

每个非空、非标题、非 `<!-- 注释 -->` 的行，必须包含一个指向 `notes/` 或 `maps/` 的链接。链接后面可以跟一句注解：

```markdown
# 业务 × 原理

## 假设检验
- [Fisher 精确检验](../notes/concept/fisher-exact-test.md) ← 小样本二分类先看这个
  - [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md)
  - [风控特征显著性](../notes/case/risk-feature-significance-fisher.md)
- [卡方检验](../notes/concept/chi-square-test.md)

## 见其他索引
- [面试准备](interview.md)
```

嵌套列表表达层级（原理下挂落地），标题表达分组，注解表达顺序和理由。

## 加一个新视角

```bash
python3 tools/new.py map <id> "<title>"
```

然后往里加链接。**不需要动任何笔记。** 一篇笔记可以同时出现在多个索引页里，这正是索引层存在的意义。

## 建议的起始索引页

| id | 视角 |
|---|---|
| `math-in-biz` | 业务 × 原理：按原理分组，原理下挂落地 case |
| `interview` | 面试准备：按领域分组，收 qa / problem / pattern |
| `leetcode` | 题单：按 pattern 分组 |

这三个只是建议，按实际内容长出来的视角才是对的。

## 维护

- 新建笔记时用 `new.py --map <id>` 直接挂进来，落在 `## 未归类` 节，之后再挪到合适的分组。
- 笔记删除后索引页里的链接会断，lint 报错，顺手删掉那行。
- `updated` 字段改动索引页时更新一下。
