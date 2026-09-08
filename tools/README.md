# tools/：新建、校验、钩子

全部零依赖，系统 `python3`（≥ 3.9）直接跑，不需要 venv。规则来源是 `../schema.json`，脚本不硬编码类型；加类型改 schema 和模板，不改脚本。

## new.py：按模板新建

```bash
python3 tools/new.py concept <id> "<title>" --domain statistics [--tags a,b] [--map <map-id>]
python3 tools/new.py <type> <id> "<title>" [--domain <d>] [--tags a,b] [--map <map-id>]
python3 tools/new.py map <id> "<title>"
```

做的事：校验 type 在 schema 里、id 合法且全库唯一、模板存在；`--domain` 时落到 `notes/<type>/<domain>/` 并把 domain 加进 tags（concept 必须给）；填占位符写文件；`--map` 时把链接追加到 `maps/<map-id>.md` 的 `## 未归类` 节并刷新其 `updated`。

## lint.py：结构校验

```bash
python3 tools/lint.py            # 校验整个仓库
python3 tools/lint.py --root DIR # 校验别的目录（测试用）
```

退出码：`0` 无错误（可有警告）、`1` 有错误、`2` 用法或环境错误。

检查项：

| 类别 | 规则 | 级别 |
|---|---|---|
| 结构 | `notes/` 下的目录都在 schema 里；类型目录只有 .md 或一层领域子目录（目录名是已登记标签）；concept 必须在领域目录里；`domain` 字段与目录一致且在 tags 中 | 错误 |
| frontmatter | 能解析（只认三种写法，见 SCHEMA §4）；无未声明字段；必填齐 | 错误 |
| id | kebab-case；= 文件名；全库唯一 | 错误 |
| 字段 | enum 取值合法；日期合法且 `updated ≥ created`；`summary` 非空 | 错误 |
| 标签 | ≥ 1；每个在 `tags.yml`；不重复 | 错误 |
| 边 | `uses` / `patterns` / `related` 目标存在、类型合规、不自指、不重复 | 错误 |
| 正文链接 | 相对路径目标存在；无 `[[wikilink]]`；图片在 `assets/`；无 `{{占位符}}` | 错误 |
| 正文结构 | 该类型的必需二级标题齐全 | 错误 |
| 索引页 | 每个非空非标题非注释行含笔记链接 | 错误 |
| 可达性 | 每篇笔记能从某个索引页沿链接到达 | 错误 |
| 附件 | 无引用的附件 | 警告 |
| inbox | 文件数 | 信息 |

## 钩子与 CI

```bash
bash tools/install-hooks.sh   # 设 core.hooksPath=tools/hooks，commit 时自动 lint
```

`.github/workflows/lint.yml` 在 push 时跑 lint + 单测。本地钩子先拦，CI 兜底。

## 测试

```bash
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

`test_lint.py` 在临时目录里搭最小知识库，逐条验证上表的规则会被拦、合法结构会通过、`new.py` 生成的文件填完 summary 能过 lint。改 lint 或 schema 后必跑。

## 扩展

- 加类型：见 `../SCHEMA.md` §9。lint 不用改；给 `test_lint.py` 加一个「该类型模板生成后能过」的用例。
- 加检查项：在 `lint.py` 对应的 `check_*` 函数里加，同时加测试用例，README 表里加一行。
- 以后可加：`backlinks.py` 生成反链报告、`export.py` 导出成 Chatbot 用的 JSONL、`review.py` 按 `last_reviewed` 拉待复习 qa。

## figures/：出图

笔记里的图都由 `tools/figures/<note-id>.py` 生成，可重跑，落到 `assets/<note-id>/<desc>.jpg`。依赖装在项目局部 venv：

```bash
python3 -m venv .venv && .venv/bin/pip install -r tools/figures/requirements.txt
.venv/bin/python tools/figures/fisher-exact-test.py     # 重出这篇的图
make figures                                            # 重出全部
```

`_style.py` 统一字体（中文用 Hiragino Sans GB）、尺寸和 `save_jpeg()`：保存成 JPEG、质量 85、宽度上限 1600 px，白底。**不要直接 `plt.savefig("x.png")`**，lint 会拦 PNG 和超过大小上限的附件（上限在 `schema.json` 的 `assets` 段）。
