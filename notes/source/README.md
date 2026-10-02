# source/：一份外部材料一篇

**放什么**：读一份外部材料（博客、论文、书、视频、课程、官方文档）留下的笔记。原文讲了什么、我怎么理解的、我对它有什么质疑。一份材料一篇。

**不放什么**：
- 自己消化后、脱离这份材料也成立的原理。那是 `../concept/`。
- 自己做过的一次落地。那是 `../case/`。材料里作者举的案例不是你的 case，留在 source 里。

## 判据

**这篇的范围是不是由一份外部材料划定的？** 是就进 source。

和"一篇一个想法"的关系：source 是这条规矩唯一的例外。一份材料往往讲五六个想法，硬拆会丢掉作者的论证顺序，所以整份留在一篇里。想法要单独被引用时再提炼（见下文）。

## 正文结构

**不设必需标题**，跟着原材料的结构走。推荐但不强制：

- 开头写清来源：作者、时间、链接、这份材料引用了哪些别的材料。
- 用三种标注区分内容来源，和全库"不编造"的规矩是一回事：

| 标注 | 含义 |
|---|---|
| 【原文】 | 来自材料本身。意译和归纳，不是逐字摘录 |
| 【解读】 | 自己的理解、补的例子、推演 |
| 【批判性阅读】 | 用材料自己的标准反过来审视它，原文里没有 |

- 材料没说、自己推测的，写明"个人推测，原文未说明"。
- 文末附术语表和参考链接，方便以后检索。

公式规则（SCHEMA.md §8.1）照常适用。图不强制；要放图同样走 `tools/figures/` + `save_jpeg()`，不要截原文的图（版权，也会撑大仓库）。

## 字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `format` | ✓ | `blog` / `paper` / `book` / `video` / `course` / `doc` |
| `url` | ✓ | 原文链接，`http(s)://` 开头，lint 会查。书没有网页就填出版社或豆瓣页 |
| `author` | | 作者，可带机构：`Lance Martin（Anthropic）` |
| `published` | | 原文发布日期 `YYYY-MM-DD`；`created` 是你写笔记的日期，两个不是一回事 |
| `related` | | 相关的 concept / case / 其他 source |
| `tags` | ✓ | 领域标签 + 主题标签 |

## 领域目录

可选，推荐放：`notes/source/<domain>/<id>.md`，domain 是 `tags.yml` 里的标签，和 concept 同一套规则（SCHEMA.md §3）。现有：

| 领域 | 放什么 |
|---|---|
| `agent-engineering/` | Agent 工程：harness、工具、skill、评测与优化 |

## id 命名

材料主题的英文 slug，不带"notes""study"这类词（类型已经说明了）：`automating-eval-hillclimbing`。同一主题读了多份材料，加作者或年份区分：`attention-is-all-you-need-2017`。

## 怎么长：source 是原料，concept 是成品

不需要一次拆完。等某个想法要单独被引用时：

1. 在 `../concept/<domain>/` 用 `new.py` 建一篇，按 concept 的深度标准重写（逐步推导、讲清为什么），不复制 source 的段落。
2. concept 的 `related` 指回这篇 source，说明出处。
3. 自己真的照着做了一次，那是一篇 case，`uses` 指向提炼出的 concept。

## 新建

```bash
python3 tools/new.py source <id> "<title>" --domain agent-engineering --tags evaluation --map agent-engineering
```

生成后填 `summary`、`format`、`url`（这三个留空 lint 会拦），再写正文。
