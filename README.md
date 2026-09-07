# zephyr-notes

个人知识库。内容很杂：数学原理怎么落到业务里、面试八股、力扣题、工程套路。所以结构上只做一件事：**把「内容」和「组织」拆开**。文件夹只按笔记类型分，主题、分类、专题一律做成索引页，靠链接组织。加一个新类目 = 加一个索引文件，已有笔记一个都不用动。

## 三层结构

```
 ┌──────────────────────────────────────────────────────────────┐
 │  索引层  maps/          「我有哪些东西」                       │
 │  纯链接，一个视角一个文件。面试 / 业务×原理 / 力扣题单……        │
 ├──────────────────────────────────────────────────────────────┤
 │  内容层  notes/         「东西本身」                           │
 │  一篇一个想法，按类型分目录：concept case problem qa pattern    │
 │  文件名即 id 永不改；笔记之间用链接互指，不靠目录表达关系        │
 ├──────────────────────────────────────────────────────────────┤
 │  契约层  schema.json + templates/ + tools/                    │
 │  规定字段和结构；模板按契约生成；lint 按契约校验               │
 └──────────────────────────────────────────────────────────────┘
```

一条知识串起来是这样：

```
  maps/math-in-biz.md ─────────┐             maps/interview.md
        │                      │                    │
        ▼                      ▼                    ▼
  concept/fisher-exact-test ◄── case/ab-test-small-sample-fisher   qa/chi2-vs-fisher
        ▲                       uses: [fisher-exact-test]               │
        └────────────────────────────────────────────────────────────────┘
                                   related: [fisher-exact-test]
```

原理只写一次，多个落地、多道面试题链过去，多个索引页各自收录。半年后同一个原理再用一次，只加一篇 case，原理和目录都不动。

## 目录

| 目录 / 文件 | 放什么 | 详细规程 |
|---|---|---|
| `notes/concept/` | 原理、定义、推导。换场景仍成立的内容 | [README](notes/concept/README.md) |
| `notes/case/` | 某原理/套路在某个业务场景的一次落地 | [README](notes/case/README.md) |
| `notes/problem/` | 一道题一篇：力扣、系统设计题 | [README](notes/problem/README.md) |
| `notes/qa/` | 一问一答的八股 | [README](notes/qa/README.md) |
| `notes/pattern/` | 在多处重复出现的套路 | [README](notes/pattern/README.md) |
| `maps/` | 索引页，只放链接 | [README](maps/README.md) |
| `inbox/` | 还没整理的随手记 | [README](inbox/README.md) |
| `templates/` | 每种类型一个模板，`new.py` 用 | [README](templates/README.md) |
| `assets/` | 图片等附件 | [README](assets/README.md) |
| `tools/` | 新建、校验、钩子 | [README](tools/README.md) |
| `schema.json` | 机器契约：类型、字段、边 | |
| `SCHEMA.md` | 契约的人话版 | [SCHEMA](SCHEMA.md) |
| `tags.yml` | 标签受控词表 | |
| `CLAUDE.md` | Agent 入口，硬规则速查 | |

## 快速开始

```bash
# 1. 建一篇原理笔记，顺手挂进「业务×原理」索引页
python3 tools/new.py concept fisher-exact-test "Fisher 精确检验" \
    --tags statistics,hypothesis-testing --map math-in-biz

# 2. 打开生成的文件，填 summary 一句话，按模板里的标题写正文

# 3. 校验（frontmatter、链接、孤儿、标签、必需标题）
python3 tools/lint.py

# 4. 提交（单人项目，直接 main）
git add -A && git commit -m "新增 concept：Fisher 精确检验" && git push
```

首次 clone 后装一次 git 钩子，commit 时自动 lint：`bash tools/install-hooks.sh`。工具零依赖，系统 `python3` 即可，不需要 venv。

## 五条规矩

1. **文件名即 id，永不改名。** 改名断链。改标题改 `title`。
2. **一篇一个想法。** 大文件既没法在想法级别互链，切 chunk 也切得稀碎。
3. **索引页只放链接。** 写了正文它就退化成按主题的大文件，前面的好处全没。lint 会拦。
4. **标签走受控词表。** `tags.yml` 没登记的标签 lint 会拦，防 `ml` / `machine-learning` 漂移。
5. **下游指上游。** case 指 concept，problem 指 pattern；上游不回指，反链由工具生成。

## 给 Agent 的操作规程

收到「把 X 记进知识库」这类请求时：

1. 读 `SCHEMA.md` §2 的类型判断表，决定这条知识是一篇还是要拆成几篇（原理 + 落地通常是两篇：`concept` + `case`）。
2. 检查 `tags.yml`，需要的标签没登记就先加一行。
3. `python3 tools/new.py <type> <id> "<title>" --tags ... --map <map-id>` 生成文件。id 用英文 slug；先 `ls notes/*/` 确认没有相近的已有笔记，有就补充它而不是新建。
4. 按模板里的必需标题写正文。`case` 必须填 `uses`。正文引用别的笔记用相对路径链接，不复制内容。
5. `python3 tools/lint.py`，全部通过再提交。
6. commit 信息中文，说清新增/修改了哪篇。

收到「整理 inbox」时按 `inbox/README.md` 的流程。要加新类型按 `SCHEMA.md` §9，先问一句是不是其实只是加个索引页。

## 编辑器

纯 markdown + 标准相对链接，任何编辑器都能用。用 Obsidian 的话把「使用 Wiki 链接」关掉，反链面板和图谱照常可用；它的本机状态文件已在 `.gitignore`。
