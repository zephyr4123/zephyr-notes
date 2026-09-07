#!/usr/bin/env python3
"""zephyr-notes 结构校验器。零依赖，Python 3.9+。

用法：
  python3 tools/lint.py            # 校验整个仓库
  python3 tools/lint.py --root DIR # 校验别的目录（测试用）
  python3 tools/lint.py --quiet    # 只输出错误和警告，不输出统计

退出码：0 无错误（可有警告）；1 有错误；2 用法/环境错误。

规则来源是 schema.json。本文件只负责执行，不定义类型和字段：
加类型、加字段改 schema.json + templates/，不改这里。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from datetime import date
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
FM_DELIM = "---"
MD_LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
WIKI_LINK = re.compile(r"\[\[[^\]]+\]\]")
PLACEHOLDER = re.compile(r"\{\{[a-z_]+\}\}")
FENCE = re.compile(r"^(```|~~~)")
HEADING2 = re.compile(r"^##\s+(.*?)\s*$")
EXTERNAL = ("http://", "https://", "mailto:", "tel:")
LATEX_BAD_DELIM = re.compile(r"\\[\(\[]")
INLINE_MATH = re.compile(r"\$([^$]*)\$")
# 正文里不许裸写的数学符号 → 该写的 LaTeX
MATH_UNICODE = {
    "χ": r"\chi", "²": "^2", "³": "^3", "≥": r"\ge", "≤": r"\le", "≠": r"\ne", "≈": r"\approx",
    "±": r"\pm", "×": r"\times", "−": "-", "√": r"\sqrt{}", "Σ": r"\sum", "∑": r"\sum", "∞": r"\infty",
    "α": r"\alpha", "β": r"\beta", "γ": r"\gamma", "δ": r"\delta", "ε": r"\varepsilon", "θ": r"\theta",
    "λ": r"\lambda", "μ": r"\mu", "π": r"\pi", "σ": r"\sigma", "Δ": r"\Delta", "Φ": r"\Phi",
}
EXEMPT_FILES = {"README.md"}


class LintError(Exception):
    """frontmatter 语法错误。"""


# ---------------------------------------------------------------- frontmatter

def split_frontmatter(text: str):
    """返回 (frontmatter 文本, 正文文本)。没有 frontmatter 时前者为 None。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != FM_DELIM:
        return None, text, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == FM_DELIM:
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1:]), i + 1
    raise LintError("frontmatter 没有闭合的 ---")


def _scalar(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1]
    return s


def parse_frontmatter(fm: str) -> dict:
    """只支持三种写法：key: 标量 / key: [a, b] / key: 后接缩进的 - item。其余报错。"""
    data: dict = {}
    lines = fm.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            raise LintError(f"frontmatter 第 {i} 行缩进不合法（只允许在 key: 下写 '  - item'）：{line.strip()!r}")
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$", line)
        if not m:
            raise LintError(f"frontmatter 第 {i} 行不是 key: value：{line!r}")
        key, rest = m.group(1), m.group(2).strip()
        if key in data:
            raise LintError(f"frontmatter 重复字段：{key}")
        if rest == "":
            items = []
            while i < len(lines) and re.match(r"^\s+-\s*", lines[i]):
                items.append(_scalar(re.sub(r"^\s+-\s*", "", lines[i])))
                i += 1
            data[key] = items
        elif rest.startswith("["):
            if not rest.endswith("]"):
                raise LintError(f"字段 {key} 的行内列表没有闭合")
            inner = rest[1:-1].strip()
            data[key] = [_scalar(x) for x in inner.split(",")] if inner else []
        else:
            data[key] = _scalar(rest)
    return data


def parse_date(s: str):
    try:
        return date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------- model

class Note:
    def __init__(self, path: Path, rel: str, type_name: str, fm: dict, body: str, body_offset: int = 0):
        self.path = path
        self.rel = rel
        self.type = type_name
        self.fm = fm
        self.body = body
        self.body_offset = body_offset   # 正文第 1 行在文件里是第 body_offset+1 行
        self.id = fm.get("id") if isinstance(fm.get("id"), str) else None
        self.links: set = set()      # 指向的其他笔记/索引页 id
        self.refs: list = []         # (字段名, 字段规格, 值列表)，延后解析
        self.dates: dict = {}


class Report:
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []
        self.stats: dict = {}

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


def rel_of(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def strip_code(body: str) -> list:
    """去掉 HTML 注释、围栏代码块和行内代码，保留行号对齐。注释是写作提示，不参与任何检查。"""
    body = HTML_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), body)
    out, in_fence = [], False
    for line in body.split("\n"):
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else re.sub(r"`[^`]*`", "", line))
    return out


# ---------------------------------------------------------------- loading

def load_schema(root: Path, rep: Report):
    p = root / "schema.json"
    if not p.exists():
        rep.error("schema.json", "不存在")
        return None
    try:
        schema = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        rep.error("schema.json", f"JSON 解析失败：{e}")
        return None
    for key in ("id_pattern", "tag_pattern", "common_fields", "types"):
        if key not in schema:
            rep.error("schema.json", f"缺少顶层字段 `{key}`")
            return None
    return schema


def load_tags(root: Path, rep: Report, pattern: str) -> dict:
    p = root / "tags.yml"
    if not p.exists():
        rep.error("tags.yml", "不存在")
        return {}
    try:
        data = parse_frontmatter(p.read_text(encoding="utf-8"))
    except LintError as e:
        rep.error("tags.yml", str(e))
        return {}
    tags = {}
    for k, v in data.items():
        if not re.match(pattern, k):
            rep.error("tags.yml", f"标签名不合法（要 kebab-case）：{k}")
        if not isinstance(v, str) or not v.strip():
            rep.error("tags.yml", f"标签 `{k}` 缺少说明")
        tags[k] = v
    return tags


def collect_notes(root: Path, schema: dict, rep: Report) -> list:
    notes: list = []
    declared_dirs = {(root / spec["dir"]).resolve(): t for t, spec in schema["types"].items()}

    notes_dir = root / "notes"
    if notes_dir.exists():
        for child in sorted(notes_dir.iterdir()):
            if child.name in EXEMPT_FILES or child.name.startswith("."):
                continue
            if child.is_dir():
                if child.resolve() not in declared_dirs:
                    rep.error(rel_of(root, child), "notes/ 下出现 schema.json 未声明的目录；加类型先改 schema.json（见 SCHEMA.md §9）")
            else:
                rep.error(rel_of(root, child), "notes/ 根下不允许放文件，笔记必须进类型目录")

    for type_name, spec in schema["types"].items():
        d = root / spec["dir"]
        if not d.exists():
            rep.error(spec["dir"], f"类型 `{type_name}` 的目录不存在")
            continue
        for p in sorted(d.iterdir()):
            if p.name in EXEMPT_FILES or p.name.startswith("."):
                continue
            r = rel_of(root, p)
            if p.is_dir():
                rep.error(r, "类型目录下不允许再建子目录（目录扁平，主题去 maps/）")
                continue
            if p.suffix != ".md":
                rep.error(r, "类型目录只放 .md；附件去 assets/")
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                rep.error(r, "不是 UTF-8 文本")
                continue
            try:
                fm_text, body, offset = split_frontmatter(text)
                if fm_text is None:
                    rep.error(r, "缺少 frontmatter（文件必须以 --- 开头）")
                    continue
                fm = parse_frontmatter(fm_text)
            except LintError as e:
                rep.error(r, str(e))
                continue
            notes.append(Note(p, r, type_name, fm, body, offset))
    return notes


# ---------------------------------------------------------------- checks

def check_fields(note: Note, schema: dict, tags: dict, rep: Report):
    spec = schema["types"][note.type]
    fields = dict(schema["common_fields"])
    for k in spec.get("skip_common", []):
        fields.pop(k, None)
    fields.update(spec.get("fields", {}))

    for key in note.fm:
        if key not in fields:
            rep.error(note.rel, f"未声明的字段 `{key}`；要加字段先改 schema.json")

    for key, f in fields.items():
        if key not in note.fm:
            if f.get("required"):
                rep.error(note.rel, f"缺少必填字段 `{key}`")
            continue
        val = note.fm[key]
        kind = f["kind"]
        required = f.get("required", False)

        if kind in ("id", "type", "string", "enum", "date"):
            if isinstance(val, list):
                rep.error(note.rel, f"字段 `{key}` 应是标量，不是列表")
                continue
            if not val.strip():
                if required:
                    rep.error(note.rel, f"必填字段 `{key}` 为空")
                continue  # 非必填字段允许留空串

        if kind == "id":
            if not re.match(schema["id_pattern"], val):
                rep.error(note.rel, f"id 不合法（要 kebab-case，小写字母数字加短横线）：{val}")
            if val != note.path.stem:
                rep.error(note.rel, f"id `{val}` 与文件名 `{note.path.stem}` 不一致；id 即文件名")
        elif kind == "type":
            if val != note.type:
                rep.error(note.rel, f"type `{val}` 与所在目录（{note.type}）不一致")
        elif kind == "enum":
            if val not in f["values"]:
                rep.error(note.rel, f"字段 `{key}` 取值 `{val}` 不在 {f['values']} 中")
        elif kind == "date":
            d = parse_date(val)
            if d is None:
                rep.error(note.rel, f"字段 `{key}` 不是合法日期（YYYY-MM-DD）：{val}")
            else:
                note.dates[key] = d
        elif kind in ("list", "tags", "reflist"):
            if not isinstance(val, list):
                rep.error(note.rel, f"字段 `{key}` 应是列表，例如 `{key}: [a, b]`")
                continue
            if any(not x.strip() for x in val):
                rep.error(note.rel, f"字段 `{key}` 里有空项")
                continue
            if len(val) != len(set(val)):
                rep.error(note.rel, f"字段 `{key}` 有重复项")
            if f.get("min") and len(val) < f["min"]:
                rep.error(note.rel, f"字段 `{key}` 至少要 {f['min']} 项")
            if kind == "tags":
                for t in val:
                    if t not in tags:
                        rep.error(note.rel, f"标签 `{t}` 未在 tags.yml 登记；先登记再用")
            elif kind == "reflist":
                for v in val:
                    if not re.match(schema["id_pattern"], v):
                        rep.error(note.rel, f"字段 `{key}` 里的引用 `{v}` 不是合法 id（写 id，不写路径）")
                    elif v == note.id:
                        rep.error(note.rel, f"字段 `{key}` 引用了自己")
                note.refs.append((key, f, val))

    c, u = note.dates.get("created"), note.dates.get("updated")
    if c and u and u < c:
        rep.error(note.rel, f"updated（{u}）早于 created（{c}）")


def check_ids(notes: list, rep: Report) -> dict:
    by_id: dict = {}
    seen: dict = {}
    for n in notes:
        if not n.id:
            continue
        if n.id in seen:
            rep.error(n.rel, f"id `{n.id}` 与 {seen[n.id]} 重复；id 全库唯一，跨目录也不能重")
            continue
        seen[n.id] = n.rel
        by_id[n.id] = n
    return by_id


def check_refs(notes: list, by_id: dict, rep: Report):
    for n in notes:
        for key, f, vals in n.refs:
            for v in vals:
                target = by_id.get(v)
                if target is None:
                    rep.error(n.rel, f"字段 `{key}` 引用的 id `{v}` 不存在")
                    continue
                targets = f.get("targets", ["*"])
                if targets != ["*"] and target.type not in targets:
                    rep.error(n.rel, f"字段 `{key}` 只能指向 {targets}，而 `{v}` 是 {target.type}")
                    continue
                n.links.add(v)


def check_math(note: Note, lines: list, rep: Report):
    """公式规范：行内 $...$；公式块 $$ 独占一行、前后空行、块内无空行；不用 \\( \\[；正文不裸写数学符号；标题不放公式。"""
    in_block = False
    for i, line in enumerate(lines):
        s, lineno = line.strip(), i + 1 + note.body_offset
        if s == "$$":
            if not in_block:
                if i > 0 and lines[i - 1].strip():
                    rep.error(note.rel, f"第 {lineno} 行：公式块 $$ 前面要空一行")
                in_block = True
            else:
                if i + 1 < len(lines) and lines[i + 1].strip():
                    rep.error(note.rel, f"第 {lineno} 行：公式块 $$ 后面要空一行")
                in_block = False
            continue
        if in_block:
            if not s:
                rep.error(note.rel, f"第 {lineno} 行：公式块里不能有空行（GitHub 会断开渲染）")
            continue
        if "$$" in line:
            rep.error(note.rel, f"第 {lineno} 行：$$ 要单独占一行做公式块；行内公式用单个 $")
            continue
        text = line.replace("\\$", "")
        if LATEX_BAD_DELIM.search(text):
            rep.error(note.rel, f"第 {lineno} 行：不用 \\( \\[ 定界符，行内用 $，公式块用 $$")
        if text.count("$") % 2:
            rep.error(note.rel, f"第 {lineno} 行：行内公式 $ 不配对（要打美元符号写 \\$）")
            continue
        if s.startswith("#") and "$" in text:
            rep.error(note.rel, f"第 {lineno} 行：标题里不放公式")
        for m in INLINE_MATH.finditer(text):
            inner = m.group(1)
            if not inner.strip():
                rep.error(note.rel, f"第 {lineno} 行：空公式 $$")
            elif inner != inner.strip():
                rep.error(note.rel, f"第 {lineno} 行：$ 内侧不能有空格（GitHub 不渲染）：${inner}$")
        if s.startswith("#"):
            continue  # 标题是纯文字，「业务 × 原理」这种排版用法不算数学
        prose = MD_LINK.sub("", INLINE_MATH.sub("", text))  # 链接文字 / alt 是纯文字，不查
        bad = [(ch, MATH_UNICODE[ch]) for ch in dict.fromkeys(prose) if ch in MATH_UNICODE]
        if bad:
            hint = "、".join(f"{c} → {t}" for c, t in bad)
            rep.error(note.rel, f"第 {lineno} 行：数学符号要写成 LaTeX 放进 $...$：{hint}")
    if in_block:
        rep.error(note.rel, "公式块 $$ 没有闭合")


def check_body(note: Note, root: Path, schema: dict, by_path: dict, rep: Report, assets_used: set):
    spec = schema["types"][note.type]
    lines = strip_code(note.body)
    assets_dir = (root / "assets").resolve()
    headings = []
    note_link_lines: set = set()

    check_math(note, lines, rep)
    if PLACEHOLDER.search(note.body):
        rep.error(note.rel, "残留模板占位符 {{...}}，没填完")
    if WIKI_LINK.search("\n".join(lines)):
        rep.error(note.rel, "不允许 [[wikilink]]，用标准 markdown 相对路径：[标题](../concept/<id>.md)")

    for lineno, line in enumerate(lines, 1 + note.body_offset):
        hm = HEADING2.match(line)
        if hm:
            headings.append(hm.group(1))
        for m in MD_LINK.finditer(line):
            is_image, target = m.group(1) == "!", m.group(3)
            if target.startswith(EXTERNAL) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if not target:
                continue
            resolved = (note.path.parent / target).resolve()
            if not resolved.exists():
                rep.error(note.rel, f"第 {lineno} 行链接目标不存在：{m.group(3)}")
                continue
            if root.resolve() not in resolved.parents:
                rep.error(note.rel, f"第 {lineno} 行链接指到仓库外：{m.group(3)}")
                continue
            if is_image and assets_dir not in resolved.parents:
                rep.error(note.rel, f"第 {lineno} 行图片必须放在 assets/：{m.group(3)}")
            if assets_dir in resolved.parents:
                assets_used.add(resolved)
            linked = by_path.get(resolved)
            if linked is not None and linked is not note:
                note.links.add(linked.id)
                note_link_lines.add(lineno)

    for h in spec.get("required_headings", []):
        if h not in headings:
            rep.error(note.rel, f"缺少必需的二级标题 `## {h}`（模板里有，别删）")

    if spec.get("body") == "links-only":
        for lineno, line in enumerate(lines, 1 + note.body_offset):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if lineno not in note_link_lines:
                rep.error(note.rel, f"第 {lineno} 行不含笔记链接；索引页每一行都必须是链接（不写正文，见 maps/README.md）")


def check_reachability(notes: list, by_id: dict, schema: dict, rep: Report):
    roots = [n.id for n in notes if schema["types"][n.type].get("body") == "links-only" and n.id]
    seen = set(roots)
    q = deque(roots)
    while q:
        cur = by_id.get(q.popleft())
        if cur is None:
            continue
        for nxt in cur.links:
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    for n in notes:
        if n.id and n.id not in seen and schema["types"][n.type].get("body") != "links-only":
            rep.error(n.rel, "孤儿：没有任何索引页能沿链接到达它。加进某个 maps/*.md，或让已收录的笔记链向它")


def check_assets(root: Path, schema: dict, assets_used: set, by_id: dict, rep: Report):
    d = root / "assets"
    if not d.exists():
        return
    for child in sorted(d.iterdir()):
        if child.name in EXEMPT_FILES or child.name.startswith("."):
            continue
        r = rel_of(root, child)
        if child.is_file():
            rep.error(r, "assets/ 根下不放文件；按笔记建子目录 assets/<note-id>/")
        elif child.name not in by_id:
            rep.error(r, f"assets/ 子目录名 `{child.name}` 不是任何笔记的 id；目录名必须等于它服务的笔记 id")
    policy = schema.get("assets", {})
    allowed = set(policy.get("allowed_ext", []))
    forbidden = set(policy.get("forbidden_ext", []))
    warn_bytes = policy.get("warn_bytes")
    max_bytes = policy.get("max_bytes")
    for p in sorted(d.rglob("*")):
        if p.is_dir() or p.name in EXEMPT_FILES or p.name.startswith("."):
            continue
        r = rel_of(root, p)
        ext = p.suffix.lower()
        if ext in forbidden:
            rep.error(r, f"不允许 {ext} 附件；位图压成 JPEG（用 tools/figures/_style.py 的 save_jpeg）")
        elif allowed and ext not in allowed:
            rep.error(r, f"附件后缀 {ext} 不在 schema.json 的 allowed_ext 里")
        size = p.stat().st_size
        if max_bytes and size > max_bytes:
            rep.error(r, f"附件 {size // 1024} KB 超过上限 {max_bytes // 1024} KB；压小或外链")
        elif warn_bytes and size > warn_bytes:
            rep.warn(r, f"附件 {size // 1024} KB 偏大（> {warn_bytes // 1024} KB），考虑压小")
        if p.resolve() not in assets_used:
            rep.warn(r, "没有任何笔记引用这个附件")


def count_inbox(root: Path) -> int:
    d = root / "inbox"
    if not d.exists():
        return 0
    return sum(1 for p in d.iterdir() if p.is_file() and p.name not in EXEMPT_FILES and not p.name.startswith("."))


# ---------------------------------------------------------------- entry

def run(root: Path) -> Report:
    rep = Report()
    schema = load_schema(root, rep)
    if schema is None:
        return rep
    tags = load_tags(root, rep, schema["tag_pattern"])
    notes = collect_notes(root, schema, rep)

    for n in notes:
        check_fields(n, schema, tags, rep)
    by_id = check_ids(notes, rep)
    by_path = {n.path.resolve(): n for n in notes if n.id}
    check_refs(notes, by_id, rep)
    assets_used: set = set()
    for n in notes:
        check_body(n, root, schema, by_path, rep, assets_used)
    check_reachability(notes, by_id, schema, rep)
    check_assets(root, schema, assets_used, by_id, rep)

    for t in schema["types"]:
        rep.stats[t] = sum(1 for n in notes if n.type == t)
    rep.stats["edges"] = sum(len(n.links) for n in notes)
    rep.stats["tags_used"] = len({t for n in notes for t in (n.fm.get("tags") or []) if isinstance(n.fm.get("tags"), list)})
    rep.stats["inbox"] = count_inbox(root)
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="zephyr-notes 结构校验")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"根目录不存在：{root}", file=sys.stderr)
        return 2

    rep = run(root)
    for e in rep.errors:
        print(f"✗ {e}")
    for w in rep.warnings:
        print(f"! {w}")
    if not args.quiet:
        s = rep.stats
        counts = "  ".join(f"{k}={v}" for k, v in s.items())
        print(("✓ " if rep.ok else "✗ ") + f"{len(rep.errors)} 错误，{len(rep.warnings)} 警告 | {counts}")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
