---
id: claude-code-mods
type: source
domain: agent-engineering
title: Claude Code Mods 入门笔记
summary: 读 claude.dev 博客《Getting started with Claude Code mods》的笔记：mod 就是装在 plugin 里的 hooks，三个心智模型（中间件链、$ 是唯一出口、状态放在宿主那边），hook 签名与观察、改写、直接作答三种动作，沙箱和与 settings hooks 的区别，Token Weather 逐步实战，分享与安全，Blast Radius 和 Replay Theater 两个示例，以及好习惯、点子和速查。
tags: [agent-engineering, claude-code]
format: blog
url: https://claude.dev/blog/getting-started-with-claude-code-mods/
author: Addy Osmani
published: 2026-10-01
related: []
status: stable
created: 2026-10-06
updated: 2026-10-06
---

# Claude Code Mods 入门笔记

> **来源**：[Getting started with Claude Code mods](https://claude.dev/blog/getting-started-with-claude-code-mods/)，Addy Osmani，claude.dev Blog（Tutorials），2026-10-01
> 原文 Markdown 版：<https://claude.dev/blog/getting-started-with-claude-code-mods.md>
> 适用版本：Claude Code **2.1.287 及以上**（mods 默认开启）。API 可能随版本变化，以本机生成的类型声明为准。
>
> 说明：本笔记是对原文的整理和精读。代码片段做过精简，只用来说明结构，完整代码请看原文。标有「**类比**」「**引申**」的部分是我的理解，不是原文内容。

---

## TL;DR：三个心智模型

1. **中间件链**：每个 hook 的签名都是 `($, e, next)`，对事件只能做三件事：观察、改写、直接作答。UI 绘制也是链上的一个事件，所以改行为和改界面是同一套机制。
2. **`$` 是唯一出口**：mod 跑在沙箱里，没有 DOM 也没有 Node，读文件、跑进程、开面板都要通过 `$`。因此 `claude plugin validate` 能静态分析出 mod 做了什么。
3. **状态放在宿主那边**：热重载会把模块扔掉重新执行，模块变量会被清空。数据要放进 `$.state`，它由 Claude Code 保管，而且是响应式的。

---

## 1. Mod 是什么

- 一个运行在 Claude Code 会话里的 JS/TS 文件，能**观察**发生了什么、**改变** Claude Code 的行为、**绘制**自定义 UI（终端和桌面 App 都可以）。
- Claude Code 原有的定制手段有 settings、权限规则、slash 命令、skills、status line。mods 比这些更深一层：可以改写甚至替换原生行为，也可以自己画界面。
- 本质上，**mods 就是装在 plugin 里的 hooks**，每个 mod 都能实时看到会话中的每一个事件。
- 不懂 API 也能上手：在 `claude` 里描述你想要的 mod，同意热重载，这一轮结束时 mod 就会出现。

## 2. 工作原理（How a mod works）

### 2.1 目录形态：就是一个普通 plugin

```text
my-mod/
├── .claude-plugin/
│   ├── plugin.json        # 标准 plugin 清单
│   └── types/             # Claude Code 加载时自动写入的类型声明
├── hooks/
│   ├── hooks.json         # { "modules": ["./my-mod.mjs"] }，一个 mod 只有一个模块
│   └── my-mod.mjs         # export function register(on, options) { ... }
├── types/index.d.ts       # 类型契约（声明 state）
└── tests/*.test.ts
```

### 2.2 Hook 签名

```js
on("tool.call", { tool: "Bash" }, async ($, e, next) => {
  return next(e);
});
```

| 部分 | 含义 |
|---|---|
| `"tool.call"` | **事件名**：关心哪一类事（这里是 Claude 要调用工具时） |
| `{ tool: "Bash" }` | **matcher（可选）**：在这类事件里再筛一道，只有工具是 Bash 时才触发 |
| `$` | mods API：ui、session、state、store、fs、process、clock、http、tool、command、model…… |
| `e` | 本次事件的输入，纯数据 |
| `next` | 把事件交给链上的下一个处理者，链的最底部是 Claude Code 的原生行为 |

**关于 matcher**（讨论中补充）：
- 不写 matcher 就会收到这类事件的全部，可以在函数里自己判断：`if (e.tool !== "Bash") return next(e);`
- 能用 matcher 就用：代码更干净，`validate` 的报告里也能直接看到，比如 `ui.render{component=AbovePrompt}`。
- 不同事件按各自最自然的维度筛选：
  - `tool.call` → `{ tool: "Bash" }`
  - `ui.render` → `{ component: "AbovePrompt" }`
  - `command.run` → `{ command: "replay" }`
- 需要匹配多个工具时（比如 Edit 和 Write），自己在函数里判断更方便。

> **类比**：像 Express 的 `app.get("/users", handler)`，`get` 对应事件类型，`"/users"` 对应 matcher。整条链则像 Koa 的洋葱模型。

### 2.3 三种动作（核心）

| 动作 | 写法 | 例子 |
|---|---|---|
| **Observe 观察** | `const r = await next(e); /* 看一眼 */ return r` | 记录每次文件编辑；每轮结束读一次数据 |
| **Rewrite 改写** | `return next({ ...e, command: safer })` | 修改链上后续环节看到的内容 |
| **Answer 直接作答** | 不调 `next`，直接 `return { deny: "…" }` | 拒绝一次工具调用；自己实现一个命令或工具 |

判断方法：**有没有调 `next`、什么时候调、传的是什么。**

### 2.4 事件覆盖面

工具调用、提交的 prompt、turn 开始/结束、会话开始/结束、slash 命令，以及 **`ui.render`**（界面每一块被绘制的时刻）。

→ **UI 也是链上的事件**：想在某个位置画东西，就拦截那个组件的 `ui.render` 并返回元素树；不想画就 `next(e)` 还回去。

### 2.5 沙箱

模块在独立沙箱中运行，没有 DOM、没有 Node，所有外部交互都通过 `$`。

### 2.6 和 settings hooks 的区别

| | settings hook | mod |
|---|---|---|
| 运行方式 | 每个事件跑一次 shell 命令 | 加载一次，常驻在会话里 |
| 通信 | stdin/stdout 传 JSON | 直接调用 `$` |
| 状态 | 无 | 有 |
| UI | 无 | 可以画随事件实时更新的 UI |
| 回调 Claude Code | 无 | 开面板、跑进程、注册 slash 命令、**注册模型可调用的工具** |

> **类比**：settings hook 像 CGI（每个请求起一个进程），mod 像常驻的服务端中间件。

### 2.7 官方自己也在用

Claude Code 的一部分功能本身就是 mod，例如 **AGENTS.md 支持**和 **`/diff` 面板**。源码和测试在 [anthropics/claude-code](https://github.com/anthropics/claude-code) 仓库的 `mods/` 目录下，是最接近生产标准的参考。

---

## 3. 实战：Token Weather

在输入框上方画一行 context window 的"天气预报"，约 80 行代码。

| 已用 | 预报 |
|---|---|
| < 25% | ☀ Clear |
| 25–49% | ☁ Cloudy |
| 50–74% | ☂ Showers |
| 75–89% | ☇ Storm |
| $\ge 90\%$ | ↯ Compact soon |

这一行依次显示：图标和天气、百分比、`已用 / 窗口`（如 `134.4k / 200k`）、最近 12 轮的迷你柱状图（`▁▂▃▄▅▆▇█`）、上一轮增量（如 `▲ +98.3k last turn`）。

### 3.0 捷径：让 Claude 帮你写

- 在 `claude` 里描述想要的效果，**只写"想看到什么"，不需要提 API**。Claude Code 内置了 mod 编写指南，负责处理 state 怎么存、怎么 validate、挂哪些事件。
- 第一次会询问是否开启本会话的热重载，同意后可以边提修改边看效果。
- ⚠️ 这样生成的 mod **只在当前会话加载，文件夹之后会被清理**。想保留，要把文件夹复制出来，按普通 plugin 安装。

### 3.1 Step 1：建目录

先 `claude --version` 确认版本 $\ge$ 2.1.287。目录结构见 2.1，`hooks.json` 只指向一个模块。

### 3.2 Step 2：先画点东西

- 目标组件是 **`AbovePrompt`**（输入框正上方那一条）。Claude Code 自己在这里什么都不画，所以适合练手。
- 元素构造函数**不是全局变量**，要通过 `const { Box, Text } = $.ui.resolve(e)` 获取。原因是每个绘制面（终端、桌面）支持的元素集合略有不同，同一个 mod 也因此能在两边都显示。也支持 JSX（factory 设为 `h`）。
- 启动：`claude --plugin-dir ./token-weather`。文件夹会被监听，**保存即热重载，不用重启**。

### 3.3 Step 3：读数据，存到 `$.state`（重点，附通俗版）

**一句话概括**：每轮结束查一下 context 用了多少，记到"小本子"上；画天气栏时翻本子画出来。

**① 数从哪来**：`$.session.usage()`，和 status line 显示的是同一组数。
- `context.tokens`：上一次回复时的输入 token 数
- `context.window`：模型窗口大小
- `context.percent`：两者之比
- 免费调用，只有请求 `breakdown` 时才会真的发一次 token 计数请求。

**② 什么时候读**：`session.start` 读一次，之后每次 `turn.complete` 读一次。两个 hook 都是 Observe 模式：

```js
const result = await next(e);   // 先让事情照常发生
if (!e.agentId) await takeReading($);  // 只记主循环的轮次，不记 subagent
return result;                  // 原样返回，什么都没改
```

**③ 存在哪：最关键的坑**
- 热重载 = **把文件扔掉，从头重新执行**。`register` 重跑，`session.start` 重新触发。
- 如果写 `let readings = []`，每次保存都会被重置成空数组，历史全部丢失。
- 正确做法是存进 `$.state`：由宿主（Claude Code）在整个会话期间保管，重载不会丢。

> **类比：寄存柜**。mod 代码随时可能"重新投胎"，但寄存柜属于 Claude Code。
> - `const readings = { plugin: "token-weather", key: "readings" }` 就是柜号
> - `$.state.get(readings)`：开柜取出本子
> - `$.state.set(readings, newValue)`：把更新后的本子放回去

**④ 类型契约：寄存前先登记**
在 `types/index.d.ts` 里扩展 `PluginState` 接口：

```ts
declare module "claude-code" {
  interface PluginState {
    "token-weather": { readings: TokenWeatherReading[] };
  }
}
```

然后在 `plugin.json` 里加上 `"types": "./types/index.d.ts"`。不声明的话 `claude plugin validate` 会报错，错误信息里会说明怎么修。（**类比**：建表前先定义表结构。）

**⑤ 白送的好处：自动重绘**
在 render hook 里调用 `$.state.get`，就等于让这块界面订阅了这个值，之后任何地方 `$.state.set`，界面都会自动重画，**不需要 `$.ui.invalidate`**。

- 记账的（`turn.complete`）只管写
- 画图的（`ui.render`）只管读
- 两边互不调用

> **类比**：像跨热重载存活的 React `useState` / signals，或者"关注了一个公众号"。

**时间线**：
1. 会话开始 → 记第 1 条 → 自动画出 ☀ Clear
2. 读了几个大文件，这轮结束 → 记第 2 条 → 自动变成 ☂ Showers
3. 改了一个颜色并保存 → 模块重跑，柜子还在 → 历史完整，只有颜色变了（如果用的是模块变量，这时只剩一条记录）

### 3.4 Step 4：画出预报（三个值得照搬的细节）

1. **props 在 `e.props` 上**。`e` 顶层只有 `component`、`surface`、`requestId`、`viewport`。
   - `e.props.hasSurvey`：有问卷要占用这一条时，用 `next(e)` 让出位置
   - `e.props.bodyColumns`：这一条的**实际宽度**（打开侧边面板时会比终端窄）。原文在宽度 $\ge 60$ 时才画柱状图和趋势
2. **没东西可画就 `return next(e)`**，把位置还给 Claude Code 和其他 mod。
3. **用单宽字符，不要用 emoji**。☀ ☁ ☂ ☇ ↯ 在任何终端字体里都能对齐。

### 3.5 Step 5：校验与测试

- `claude plugin validate ./token-weather`：静态报告 hooks、`$` 调用、state 读写。（得益于"`$` 是唯一出口"。）
- `claude plugin test ./token-weather`：在真实运行时里跑 `*.test.ts`（从 `claude-code/testing` 导入 `describe/test/expect`）。
- **巧妙之处：mock 用的就是中间件链本身**。测试里用 `on` 注册的 hook 排在 mod **之后**，正好占住原本 Claude Code 原生行为的位置。所以只要 `on("session.usage", () => 假数据)`，就能完全控制 `$.session.usage()` 的返回值。
- 测试流程：`$.session.start` → `$.ui.mount` 挂载 `AbovePrompt` → `ui.find` 断言出现 "Clear" → 改 tokens，触发 `$.turn.complete` → 断言 "Showers"、"67% of context"、"▲ +98.3k last turn"。这同时验证了自动重绘。

### 3.6 Step 6：分享

本地 marketplace = 一个带 `.claude-plugin/marketplace.json` 的文件夹：

```bash
claude plugin marketplace add ./my-mods
claude plugin install token-weather@my-mods --scope user
```

---

## 4. 分享与安全（Sharing your mod）

- 一个带 marketplace 文件的 GitHub 仓库就是一个 marketplace，更新时正常 push 即可。
- 别人在 Claude Code 里安装：
  ```text
  /plugin marketplace add your-org/my-mods
  /plugin install token-weather@my-mods
  /reload-plugins
  ```
  没有出现的话重启 Claude Code。
- ⚠️ **安全**：mod 在本机运行，权限和 Claude Code 相同，作者是发布者而不是 Anthropic。要像装 npm 包一样，**先读仓库，只装信得过的人写的**。
- 可以提交到 Claude 目录：[claude.ai/directory/manage](https://claude.ai/directory/manage)。

---

## 5. Blast Radius：危险命令先拦，看清楚再决定

**功能**：Bash 要执行 `rm -rf`、`git reset --hard`、`git clean`、强制推送、数据库迁移时，先扣住调用，算出影响范围，打开带 **Proceed(1) / Cancel(2)** 的面板。取消时 Claude 收到附带原因的拒绝，继续则按原样执行。

> **类比**：小区保安。普通车直接放行，危险品车先拦下来，查清楚装了什么，给业主看清单，业主同意才放。

**hooks**：`tool.call`（Bash）+ `ui.render`（`Pane`）+ `ui.render`（`AbovePrompt`，作为降级位置）

**流程（用的是 Answer 动作）**：

```text
classify(command)
 ├─ 不危险 → next(e)
 └─ 危险 → measure（演习）→ $.ui.open 打开面板 → 等待按键
            ├─ Proceed → next(e)
            └─ Cancel  → return { deny: "用户取消了；这条命令本来会……" }
```

**学到的技巧**：
1. **`$.process.run` 做演习**：调用工具自带的 dry run，比如 `git status --porcelain`、`git clean -n`、`git log HEAD..origin/main`、`showmigrations`。参数用 **argv 数组**传入，路径里的字符不会被当作 shell 代码执行，避免命令注入。
2. **扣住调用**：每个 hook 每次调用只有 **10 秒**自己的运行时间，但**在 `$` 调用里等待的时间不计入**。所以用循环 `await $.process.run(["sleep", "0.25"])` 轮询，直到按钮的 `onPress` 写入决定。`next.signal.aborted`（用户按 Esc）时退出循环。
3. **带快捷键的按钮**：`Button({ label: "Proceed", hotkey: "1", onPress })`，支持点击、Tab+Enter、数字键三种操作。
4. **降级**：`$.ui.open` 返回 `isPlaced: false`（终端太窄）时，把同一份报告画到 `AbovePrompt`。

**⚠️ 局限**：它只是安全网，不是权限系统。它读的是命令文本，所以 `$(…)`、别名、脚本内部调用的 `rm` 都会漏过去。**需要硬性禁止时请用权限规则。**

---

## 6. Replay Theater：回放上一轮的所有改动

**功能**：记录一轮中所有 Edit/Write 调用（文件、改前、改后）。这一轮结束后输入框上方出现提示，按 `r` 或输入 `/replay`，在面板里逐步查看 diff，有步骤条和 Prev / Next / Close 按钮。

**纯观察**，从不拦截或修改编辑：

| hook | 作用 |
|---|---|
| `tool.call`（不带 matcher） | 如果是 Edit/Write，生成步骤放进 `pending`，然后 `next(e)` 原样放行 |
| `turn.start` | 清空 `pending`（只针对主循环） |
| `turn.complete` | 把 `pending` 转成 `replay`（只针对主循环） |
| `session.start` | `$.command.register({ name: "replay", ... })` 注册 slash 命令 |
| `command.run`（`{ command: "replay" }`） | 打开面板，返回 "Replaying" 或 "No edits" |

**学到的技巧**：
1. **事件配对**：`turn.start` 和 `turn.complete` 像一对括号，保证每轮对应一份回放。用 `e.agentId` 排除 subagent，否则分组会乱。
2. **注册 slash 命令**分两步：先在 `session.start` 里 register，再在 `command.run` 里作答。
3. **读取 Write 的旧内容**：Write 调用里只有新内容。但 `tool.call` hook **在工具执行前**运行，这时用 `$.fs.read` 读到的就是覆盖前的旧文件，所以 diff 是真实的。→ 理解 hook 在链上的位置，就知道每个时刻能拿到什么数据。
4. **位置交给界面决定**：全屏时停靠在右侧，80 列时在输入框上方展开，mod 画的是同一棵树。（Blast Radius 是自己判断 `isPlaced` 来降级，两种做法都可以。）

---

## 7. 三个 mod 对比

| | 动作 | 画在哪 | 新能力 | 出发点 |
|---|---|---|---|---|
| Token Weather | 观察 | 输入框上方 | `$.state`、自动重绘 | context 还剩多少？ |
| Blast Radius | 直接作答（拒绝） | 面板 / 降级到上方 | 跑进程、扣住调用、按钮 | 这条命令要删什么？ |
| Replay Theater | 观察 | 面板 / 上方 | 事件配对、注册命令、读文件 | Claude 刚才改了什么？ |

---

## 8. 四个好习惯

1. **以自动生成的类型为准**：`.claude-plugin/types/` 是当前版本的权威参考，编辑器和 `tsc -p` 直接可用。API 会随版本变化，教程可能过时，这份声明不会。
2. **props 从 `e.props` 读**：写成 `e.bodyColumns` 不会报错，只会得到 `undefined`。
3. **按"随时会热重载"来设计**：数据放 `$.state`，不放模块变量。
   - **引申（非原文）**：`session.start` 会被反复触发，里面的初始化最好能安全地重复执行。
4. **画面不出来就看日志**：`claude --debug`，找"hook 返回的元素树不合法"那一行。非法的元素树会被悄悄丢弃，表面上没有任何报错。

---

## 9. 可以做什么 mod（原文点子 + 拆解）

| 点子 | 事件 | 动作 | 关键 API |
|---|---|---|---|
| 费用 / 限额表 | `turn.complete` | 观察 | `$.session.usage()`、`$.ui.status` |
| 每条 prompt 自动附上团队规范 | `prompt.submit` | **改写** | `next({ ...e, ... })` |
| 列出本会话 Claude 读过的所有文件 | `tool.call`（Read） | 观察 | `$.state` + 面板 |
| 长任务完成后弹提醒 | `turn.start` / `turn.complete` | 观察 | `$.ui.toast` |
| 针对自己技术栈的守卫（生产 kubectl、`terraform apply`） | `tool.call`（Bash） | 直接作答 | 参照 Blast Radius |

> 三种动作里，原文唯一没有完整示例的是"改写"，`prompt.submit` 这个点子正好可以用来练手。

---

## 10. 速查

**命令**
```bash
claude --version                        # ≥ 2.1.287
claude --plugin-dir ./my-mod            # 加载本地 mod，保存即热重载
claude --debug                          # 排查画面不显示
claude plugin validate ./my-mod         # 静态校验
claude plugin test ./my-mod             # 运行 *.test.ts
claude plugin marketplace add <path|org/repo>
claude plugin install <name>@<marketplace> --scope user
```

**常用 `$` API（原文出现过的）**
- `$.ui.resolve(e)` / `$.ui.open` / `$.ui.mount`（测试用）/ `$.ui.status` / `$.ui.toast`
- `$.session.usage()` / `$.session.cwd()`
- `$.state.get` / `$.state.set`
- `$.process.run([...argv])`
- `$.fs.read`
- `$.command.register`

**常用事件**：`session.start`、`turn.start`、`turn.complete`、`tool.call`、`prompt.submit`、`command.run`、`ui.render`

**组件**：`AbovePrompt`（输入框上方）、`Pane`（侧边面板）

---

## 相关链接

- 原文：<https://claude.dev/blog/getting-started-with-claude-code-mods/>
- 官方 mods 源码：<https://github.com/anthropics/claude-code>（`mods/` 目录）
- Claude Code 文档：<https://code.claude.com/docs>
- Mods 展示页：<https://claude.dev/mods/>
- Claude 目录提交：<https://claude.ai/directory/manage>
