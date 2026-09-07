# SCHEMA：知识库契约

本文解释规则的**含义**；字段定义的**机器真值在 `schema.json`**，`tools/lint.py` 只读那个文件。两边不一致以 `schema.json` 为准，并立刻修本文。

## 1. 三层结构

```
 maps/        索引层：只有链接。一个视角一个文件。加类目 = 加文件，笔记不动。
 notes/       内容层：一篇一个想法，按类型分目录。文件名即 id，永不改名。
 schema.json  契约层：类型、字段、边的规则。templates/ 按它生成，tools/ 按它校验。
 templates/
 tools/
```

## 2. 类型（type）

类型是**有限枚举**，决定笔记物理上放哪个目录。选型只问一个问题：

| type | 目录 | 判断标准 | 一句话 |
|---|---|---|---|
| `concept` | `notes/concept/` | **换一个业务场景，这段话还成立** | 原理、定义、推导 |
| `case` | `notes/case/` | 只对某次具体落地成立 | 某原理/套路在某场景怎么用的 |
| `problem` | `notes/problem/` | 有题面、有输入输出 | 力扣 / 系统设计题 |
| `qa` | `notes/qa/` | 一问一答、准备背的 | 面试八股 |
| `pattern` | `notes/pattern/` | 在 ≥ 2 篇 problem/case 里重复出现的套路 | 滑动窗口、分布式锁 |
| `map` | `maps/` | 不是内容，是目录 | 索引页 |

拿不准就进 `inbox/`，不要硬归。类型永远不按主题加（「面试」「数学」是索引页，不是类型）。

## 3. id 与文件名

- `id` = 文件名去掉 `.md`，全库唯一（跨目录也不能重），格式 `^[a-z0-9]+(-[a-z0-9]+)*$`（小写字母数字 + 短横线）。
- **id 一旦创建永不改**。改名会断链。标题想改就改 `title`。
- 英文 slug，中文放 `title`。`problem` 类建议 `lc-0003-longest-substring` 这种带题号的 id。
- 类型目录下不允许再建子目录，不允许放非 `.md` 文件（图片去 `assets/`）。

## 4. Frontmatter

每篇笔记以 `---` 包住的 frontmatter 开头。**只支持以下三种写法**（lint 的解析器就这么大，故意的，够用且机器好查）：

```yaml
key: 值                 # 标量；含特殊字符时加引号
key: [a, b, c]          # 行内列表
key:                    # 块列表
  - a
  - b
```

不支持嵌套 mapping、多行字符串。`schema.json` 里没声明的字段直接报错。

### 4.1 公共字段（所有类型）

| 字段 | 必填 | 规则 |
|---|---|---|
| `id` | ✓ | 见 §3 |
| `type` | ✓ | 与所在目录一致 |
| `title` | ✓ | 人读的标题，可中文 |
| `summary` | ✓ | **一句话**说这篇讲什么。索引页和 Chatbot 都靠它 |
| `tags` | ✓ | ≥ 1 个，每个都必须在 `tags.yml` 登记 |
| `related` | | 泛用的边：任意类型的 id 列表。「有关系但说不清是什么关系」用它 |
| `status` | ✓ | `draft` 还在写 / `stable` 可以信 / `deprecated` 过时了但留着 |
| `created` | ✓ | `YYYY-MM-DD` |
| `updated` | ✓ | `YYYY-MM-DD`，不能早于 `created` |

`map` 类型免 `tags` / `status` / `created` / `related`。

### 4.2 类型专属字段

| type | 字段 | 必填 | 规则 |
|---|---|---|---|
| `concept` | `aliases` | | 别名列表，如 `[费舍尔精确检验, Fisher's exact test]` |
| `case` | `uses` | ✓ ≥ 1 | 用了哪些 `concept` / `pattern`。**这是 case 的核心边** |
| `problem` | `platform` | ✓ | `leetcode` / `codeforces` / `nowcoder` / `other` |
| | `number` | | 题号，字符串 |
| | `difficulty` | ✓ | `easy` / `medium` / `hard` |
| | `url` | | 题目链接 |
| | `patterns` | | 用到的 `pattern` id 列表 |
| `qa` | `difficulty` | | 同上 |
| | `last_reviewed` | | 上次复习日期，以后做间隔复习 |
| `pattern` | 无 | | 例题靠反向链接（哪些 problem/case 指向它） |

## 5. 边（链接）

| 边 | 写在哪 | 方向 | 语义 |
|---|---|---|---|
| `uses` | case 的 frontmatter | case → concept/pattern | 「这次落地用了它」 |
| `patterns` | problem 的 frontmatter | problem → pattern | 「这题是这个套路」 |
| `related` | 任意 frontmatter | 任意 | 「有关，说不清什么关系」 |
| 正文链接 | 正文 | 任意 | 行文中自然引用 |
| 索引页链接 | maps/ 正文 | map → 任意 | 「这个视角下收录它」 |

规则：
- **下游指上游，上游不回指**。case 指 concept，concept 不用列谁用了它；反向关系由工具/编辑器的反链生成。
- 正文链接用**标准 markdown 相对路径**：`[Fisher 精确检验](../concept/fisher-exact-test.md)`。**不用 `[[wikilink]]`**（GitHub 不渲染），lint 会拦。
- 图片：`![说明](../../assets/<note-id>-<desc>.png)`，文件必须在 `assets/`。
- 所有链接目标必须存在，否则报错。

## 6. 索引页（maps/）的正文规则

正文里每一个非空、非标题、非 HTML 注释的行，**都必须包含一个指向笔记或索引页的链接**。可以在链接后面加一句「为什么放这儿 / 先看哪个」：

```markdown
## 假设检验
- [Fisher 精确检验](../notes/concept/fisher-exact-test.md) ← 小样本二分类先看这个
  - [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md)
```

违反就报错。这是防止索引页退化成「按主题的大文件」的唯一闸。

## 7. 可达性（孤儿检查）

每篇 `notes/` 下的笔记都必须能从某个索引页**沿链接到达**（直接收录，或被某篇已收录的笔记链到）。到不了的叫孤儿，报错。修法：加进某个 map，或让相关笔记链向它。`tools/new.py --map <id>` 建笔记时可直接挂进索引页。

## 8. 正文结构

每种类型有**必须出现的二级标题**（`schema.json` 的 `required_headings`），模板已带。为的是同类笔记长得一样，人好扫、机器好切 chunk。标题之外可以随意加节。

### 8.1 数学公式（lint 会查）

渲染器（GitHub、Obsidian）对公式写法很挑剔，错一点就整段不渲染。规则：

- **只用两种定界符**：行内 `$...$`；独立公式 `$$` 单独占一行，前后各空一行，块内不能有空行。不用 `\(` `\[`。
- **凡是数学都进 `$`**：变量、下标、比较、希腊字母。正文里不裸写 χ ² ≥ ≤ ≈ × − Σ α Δ 这类 Unicode 符号，一律 `\chi^2` `\ge` `\le` `\approx` `\times` `-` `\sum` `\alpha` `\Delta`。
- **`$` 内侧紧贴内容**：`$p = 0.03$` 对，`$ p = 0.03 $` 错，GitHub 不渲染后者。
- **标题、链接文字、图片 alt 里不放公式**；frontmatter 不渲染公式，`title` / `summary` 用文字描述。
- 表格单元格可以放行内公式，但公式里别出现 `|`。
- 要打美元符号写 `\$`。
- 分数 `\frac`、二项式 `\binom`、公式里的文字 `\text{obs}`、多行对齐 `\begin{aligned}...\end{aligned}`。

```markdown
在 $H_0$ 下，$p = P\big(\chi^2_{(1)} \ge \chi^2_{\text{obs}}\big)$。

$$
\chi^2=\sum_{i,j}\frac{(O_{ij}-E_{ij})^2}{E_{ij}}
$$
```

## 9. 加一个新类型的流程

1. `schema.json` 的 `types` 里加一项：`dir`、`fields`、`required_headings`
2. `mkdir notes/<type>`，写 `notes/<type>/README.md`（照别的目录的写法）
3. `templates/<type>.md`（frontmatter 字段和 schema 对齐，正文带必需标题）
4. `python3 tools/lint.py` 通过，`python3 -m unittest discover -s tools` 通过
5. 本文 §2 / §4.2 加一行

加类型要动 4 个地方，所以要想清楚再加。加索引页只要 1 个文件，优先考虑「这其实是不是一个新视角而不是新类型」。

## 10. 给 Chatbot / RAG 的说明

- 一篇笔记 = 一个 chunk 单元；frontmatter 原样作为 metadata。
- 按 `type` 过滤 = 按知识种类检索；按 `tags` 过滤 = 按领域检索。
- `uses` / `patterns` / `related` 是显式的图边，检索时可以沿边扩展一跳。
- `summary` 可以单独做一层粗召回。
- `maps/` 直接回答「关于 X 我有哪些东西」。
