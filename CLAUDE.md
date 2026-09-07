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

## 常用命令

```bash
python3 tools/new.py concept fisher-exact-test "Fisher 精确检验" --tags statistics,hypothesis-testing --map math-in-biz
python3 tools/new.py map interview "面试准备"
python3 tools/lint.py
python3 -m unittest discover -s tools -p 'test_*.py'
```

## 协作方式

单人项目，直接在 `main` 上 commit + push，不开分支。commit 信息用中文。每个目录的 `README.md` 是该目录的操作规程，处理哪个目录的文件就先读哪个 README。
