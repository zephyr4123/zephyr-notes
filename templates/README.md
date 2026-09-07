# templates/：笔记模板

`tools/new.py` 按类型取这里的模板生成文件。**每个类型一个模板，文件名 = 类型名**：`concept.md`、`case.md`、`problem.md`、`qa.md`、`pattern.md`、`map.md`。

## 占位符

| 占位符 | 替换为 |
|---|---|
| `{{id}}` | 命令行给的 id |
| `{{title}}` | 命令行给的标题 |
| `{{date}}` | 今天，`YYYY-MM-DD` |
| `{{tags}}` | `--tags` 给的列表，逗号分隔；没给则为空 |

生成后文件里不能残留 `{{...}}`，lint 会报。

## 模板必须和契约对齐

- frontmatter 字段 = `schema.json` 里该类型的公共字段 + 专属字段。多了 lint 报未声明，少了 lint 报缺失。
- 正文二级标题 ⊇ 该类型的 `required_headings`。
- `<!-- ... -->` 注释是写作提示，可以留着也可以删，lint 不管。

改 `schema.json` 加了字段，**同一次 commit 里改模板**，`tools/test_lint.py` 里有用例会拿模板生成笔记跑 lint，不对齐测试就红。

## 有意留空让 lint 报的字段

`summary: ""` 和（没给 `--tags` 时的）`tags: []` 故意留空。这两个字段对索引页和 Chatbot 太重要，宁可让 lint 拦住，也不允许空着提交。
