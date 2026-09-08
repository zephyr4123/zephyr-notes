#!/usr/bin/env python3
"""按模板新建一篇笔记或索引页。零依赖。

用法：
  python3 tools/new.py concept <id> "<title>" --domain statistics [--tags a,b] [--map <map-id>]
  python3 tools/new.py <type> <id> "<title>" [--domain <d>] [--tags a,b] [--map <map-id>]
  python3 tools/new.py map <id> "<title>"

做的事：
  1. 校验 type 在 schema.json 里、id 合法且全库唯一、模板存在
  2. 用 templates/<type>.md 填占位符生成文件
  3. --map 时把链接追加到 maps/<map-id>.md 的「## 未归类」节，并刷新其 updated

生成后 summary（和没给 --tags 时的 tags）是空的，lint 会拦，填完再提交。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
UNSORTED_HEADING = "## 未归类"


class NewError(Exception):
    pass


def load_schema(root: Path) -> dict:
    p = root / "schema.json"
    if not p.exists():
        raise NewError(f"找不到 {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def find_existing(root: Path, schema: dict, note_id: str):
    for spec in schema["types"].values():
        d = root / spec["dir"]
        if not d.exists():
            continue
        for p in d.glob(f"**/{note_id}.md"):
            return p
    return None


def render(template: str, **vals) -> str:
    out = template
    for k, v in vals.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def attach_to_map(root: Path, schema: dict, map_id: str, note_path: Path, title: str, today: str):
    map_path = root / schema["types"]["map"]["dir"] / f"{map_id}.md"
    if not map_path.exists():
        raise NewError(f"索引页不存在：{map_path.relative_to(root)}；先 `new.py map {map_id} \"标题\"` 建它")
    text = map_path.read_text(encoding="utf-8")
    rel = Path(*(["..", *note_path.relative_to(root).parts])).as_posix()
    line = f"- [{title}]({rel})"
    if line in text:
        return map_path
    if UNSORTED_HEADING in text:
        head, tail = text.split(UNSORTED_HEADING, 1)
        # 在「## 未归类」这一节末尾（下一个 ## 之前）追加
        m = re.search(r"\n(?=## )", tail)
        if m:
            section, rest = tail[: m.start()], tail[m.start():]
        else:
            section, rest = tail, ""
        section = section.rstrip("\n") + "\n" + line + "\n"
        text = head + UNSORTED_HEADING + section + rest
    else:
        text = text.rstrip("\n") + f"\n\n{UNSORTED_HEADING}\n{line}\n"
    text = re.sub(r"^updated: .*$", f"updated: {today}", text, count=1, flags=re.M)
    map_path.write_text(text, encoding="utf-8")
    return map_path


def create(root: Path, type_name: str, note_id: str, title: str, tags=None, map_id=None, today=None, domain=None) -> Path:
    schema = load_schema(root)
    today = today or date.today().isoformat()
    if type_name not in schema["types"]:
        raise NewError(f"未知类型 `{type_name}`；可选：{', '.join(schema['types'])}")
    dom = schema.get("domains", {})
    if domain:
        if type_name not in dom.get("allowed_for", []):
            raise NewError(f"类型 `{type_name}` 不支持领域目录")
        if not re.match(schema["id_pattern"], domain):
            raise NewError(f"domain 不合法（要 kebab-case）：{domain}")
        tags = list(tags or [])
        if domain not in tags:
            tags.insert(0, domain)
    elif type_name in dom.get("required_for", []):
        raise NewError(f"类型 `{type_name}` 必须指定 --domain（tags.yml 里的一个标签，如 statistics / probability）")
    if not re.match(schema["id_pattern"], note_id):
        raise NewError(f"id 不合法（要 kebab-case，小写字母数字加短横线）：{note_id}")
    if not title.strip():
        raise NewError("标题不能为空")
    existing = find_existing(root, schema, note_id)
    if existing is not None:
        raise NewError(f"id `{note_id}` 已存在：{existing.relative_to(root)}；补充它，或换一个 id")
    tpl = root / "templates" / f"{type_name}.md"
    if not tpl.exists():
        raise NewError(f"模板不存在：{tpl.relative_to(root)}")

    out_dir = root / schema["types"][type_name]["dir"]
    if domain:
        out_dir = out_dir / domain
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{note_id}.md"
    text = render(tpl.read_text(encoding="utf-8"),
                  id=note_id, title=title, date=today, tags=", ".join(tags or []), domain=domain or "")
    if domain and "domain:" not in text.split("---")[1]:
        text = re.sub(r"^(type: .*)$", lambda m: m.group(1) + f"\ndomain: {domain}", text, count=1, flags=re.M)
    out.write_text(text, encoding="utf-8")

    if map_id:
        if type_name == "map":
            raise NewError("索引页不挂进别的索引页，手动在正文里加链接")
        attach_to_map(root, schema, map_id, out, title, today)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="按模板新建笔记 / 索引页")
    ap.add_argument("type")
    ap.add_argument("id")
    ap.add_argument("title")
    ap.add_argument("--tags", default="", help="逗号分隔，须在 tags.yml 登记")
    ap.add_argument("--map", dest="map_id", help="顺手挂进这个索引页的「## 未归类」节")
    ap.add_argument("--domain", help="领域子目录（tags.yml 里的标签）；concept 必填，如 statistics / probability")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args(argv)
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    try:
        out = create(args.root.resolve(), args.type, args.id, args.title, tags, args.map_id, domain=args.domain)
    except NewError as e:
        print(f"✗ {e}", file=sys.stderr)
        return 2
    rel = out.relative_to(args.root.resolve())
    print(f"✓ 已生成 {rel}")
    if args.map_id:
        print(f"  已挂进 maps/{args.map_id}.md 的「未归类」节，记得挪到合适分组")
    print("  下一步：填 summary 一句话" + ("" if tags else "、填 tags") + "，按模板标题写正文，然后 python3 tools/lint.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
