# zephyr-notes · Agent 入口

这是一个结构化的个人知识库，不是普通的 markdown 堆。动任何文件之前先读 `README.md` 和 `SCHEMA.md`。

## 硬规则

1. **新建笔记只用 `python3 tools/new.py`**，不要手建文件。它按模板生成、校验 id、可直接挂进索引页。
2. **提交前必跑 `python3 tools/lint.py`**，有错不提交。lint 是唯一裁判。
3. **索引页（`maps/`）只放链接**，一行一个链接，不写正文。
4. **一篇笔记一个想法**。判断标准：「换一个业务场景这段话还成立吗」→ 成立进 `concept`，不成立进 `case`。
5. **id 即文件名，永不改名。** 不复制别的笔记内容，用链接。
6. **标签必须在 `tags.yml` 登记**，没有就先加一行再用。
7. 拿不准类型就放 `inbox/`，不要硬归。
8. **绝不编造。** 关于业务的每句话都要能在用户给的材料里找到依据；数学推算和对同一数据的补算可以，但要标明"补算"；猜测标"待验证"。用户的前提错了就如实写进复盘，不顺着说。
9. **图文并茂。** 写 concept / case 时先想哪些数据能画成图（分布、观测 vs 期望、置信区间、方法对比），用 `.venv` 里的 matplotlib / scipy 按真实数据出图，直观的表也算。出图脚本放 `tools/figures/<note-id>.py`，可重跑。
10. **图只存 JPEG。** 出图统一走 `tools/figures/_style.py` 的 `save_jpeg()`，落到 `assets/<note-id>/<desc>.jpg`（一篇一个子目录）。不放 PNG，附件超限 lint 会拦，仓库不能随 commit 越滚越大。
11. **公式写规范 LaTeX。** 行内 `$...$`，公式块 `$$` 独占一行且前后空行；正文不裸写 χ ² ≥ × Σ α 这类符号，全部进 `$` 用 `\chi^2` `\ge` `\times` `\sum` `\alpha`；`$` 内侧不留空格；标题里不放公式。细则见 SCHEMA.md §8.1，lint 会拦。

## 常用命令

```bash
python3 tools/new.py concept fisher-exact-test "Fisher 精确检验" --tags statistics,hypothesis-testing --map math-in-biz
python3 tools/new.py map interview "面试准备"
python3 tools/lint.py
python3 -m unittest discover -s tools -p 'test_*.py'
python3 -m venv .venv && .venv/bin/pip install -r tools/figures/requirements.txt   # 出图环境，一次
.venv/bin/python tools/figures/<note-id>.py                                        # 重出某篇的图
```

## 协作方式

单人项目，直接在 `main` 上 commit + push，不开分支。commit 信息用中文。每个目录的 `README.md` 是该目录的操作规程，处理哪个目录的文件就先读哪个 README。
