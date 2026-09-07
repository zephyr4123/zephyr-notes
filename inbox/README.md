# inbox/：还没整理的随手记

**目的**：降低「记下来」的门槛。想到什么、看到什么，扔一个文件进来就行，不要格式、不要 frontmatter、不要想类型。lint 不检查这里，只报个数。

**代价**：必须定期清空。inbox 堆到 20 个以上，说明整理流程断了。

## 怎么记

```bash
echo "Fisher 精确检验今天在 AB 实验里用上了，样本只有 40，卡方不行……" > inbox/2026-09-07-fisher-ab.md
```

文件名建议 `YYYY-MM-DD-<几个词>.md`，方便按时间清。内容随便写。

## 怎么整理（Agent 收到「整理 inbox」时按这个走）

对 inbox 里的每个文件：

1. **读完，判断它是几篇。** 一段「原理 + 我怎么用的」通常是两篇：`concept` + `case`。
2. **查重。** `ls notes/*/` 和 `grep -ril <关键词> notes/`，已有相近笔记就补充进去，不新建。
3. **按 `notes/README.md` 的判断树定类型**，用 `python3 tools/new.py` 建文件，`--map` 挂进合适的索引页。
4. **把内容搬过去**，按模板的必需标题重组。case 填 `uses`。需要的标签先在 `tags.yml` 登记。
5. **`python3 tools/lint.py` 通过**后删掉 inbox 里的原文件。
6. 一次 commit 一个 inbox 条目的整理结果，commit 信息写清「整理 inbox：xxx → concept/xxx + case/xxx」。

拿不准类型的，留在 inbox 并在文件顶部写一行 `<!-- 待定：可能是 qa 也可能是 concept，因为… -->`，下次再看。不要为了清空 inbox 硬归。
