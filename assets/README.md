# assets/：附件

图片、PDF、数据文件都放这里，**扁平，不分子目录**。

## 命名

`<note-id>-<描述>.<ext>`：`fisher-exact-test-contingency-table.png`。看文件名就知道属于哪篇笔记；笔记删了附件好找。

## 在笔记里引用

从 `notes/<type>/` 引用：

```markdown
![2×2 列联表](../../assets/fisher-exact-test-contingency-table.png)
```

从 `maps/` 引用（索引页一般不放图）：`../assets/...`。

## 规则

- 链接目标必须存在，否则 lint 报错。
- 没有任何笔记引用的附件 lint 报警告（不阻断），定期清。
- 大文件（> 5 MB）先想想是不是真要进 git；能外链就外链。
- 截图去掉敏感信息再放，这是公开仓库。
