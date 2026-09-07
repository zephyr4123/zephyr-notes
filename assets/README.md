# assets/：附件

图片、PDF、数据文件都放这里，**一篇笔记一个子目录**：`assets/<note-id>/<desc>.<ext>`。目录名必须等于笔记 id，根下不放文件（lint 会查）。

## 命名

`assets/<note-id>/<描述>.<ext>`：`assets/fisher-exact-test/pmf.jpg`。目录即归属，笔记删了整个目录一起删。一张图被多篇笔记引用时，放在"主要讲它"的那篇名下。

## 在笔记里引用

从 `notes/<type>/` 引用：

```markdown
![H0 下的超几何分布](../../assets/fisher-exact-test/pmf.jpg)
```

从 `maps/` 引用（索引页一般不放图）：`../assets/...`。

## 规则

- 链接目标必须存在，否则 lint 报错。
- 没有任何笔记引用的附件 lint 报警告（不阻断），定期清。
- 大文件（> 5 MB）先想想是不是真要进 git；能外链就外链。
- 截图去掉敏感信息再放，这是公开仓库。

## 图片格式与大小（lint 会查）

- 位图**只放 JPEG**（`.jpg`）。PNG / BMP / TIFF 直接报错。矢量图 `.svg` 可以。
- 单个附件超过 300 KB 警告、超过 1 MB 报错；上限写在 `schema.json` 的 `assets` 段。
- 图由 `tools/figures/<note-id>.py` 生成，`save_jpeg(fig, "<note-id>", "<desc>")` 自动落到对应子目录；改图改脚本重跑，别手工导出。
