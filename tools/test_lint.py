"""lint.py / new.py 的单测。在临时目录里搭最小知识库，逐条验证规则。

运行：python3 -m unittest discover -s tools -p 'test_*.py' -v
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import new   # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TODAY = "2026-09-07"

CONCEPT = """---
id: fisher-exact-test
type: concept
domain: statistics
title: Fisher 精确检验
summary: 2×2 列联表小样本下的精确 p 值。
tags: [statistics, hypothesis-testing]
aliases: [费舍尔精确检验]
related: []
status: stable
created: 2026-09-01
updated: 2026-09-07
---

# Fisher 精确检验

## 解决什么问题
小样本。

## 原理
超几何分布。

## 适用边界
期望频数 < 5。
"""

CASE = """---
id: ab-test-small-sample-fisher
type: case
title: 小样本 AB 用 Fisher 判显著
summary: 新按钮只有 40 个样本，卡方不满足前提，改用 Fisher。
tags: [ab-test, statistics]
uses: [fisher-exact-test]
related: []
status: draft
created: 2026-09-07
updated: 2026-09-07
---

# 小样本 AB

## 背景
40 人。

## 为什么用它
见 [Fisher 精确检验](../concept/statistics/fisher-exact-test.md)。

## 怎么做的
`scipy.stats.fisher_exact`。

## 结果与复盘
显著。
"""

MAP = """---
id: math-in-biz
type: map
title: 业务 × 原理
summary: 按原理分组，原理下挂落地。
updated: 2026-09-07
---

# 业务 × 原理

<!-- 每一行都必须是链接 -->

## 假设检验
- [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md) ← 先看这个
"""


class VaultCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="zephyr-notes-test-"))
        for f in ("schema.json", "tags.yml"):
            shutil.copy(REPO / f, self.tmp / f)
        shutil.copytree(REPO / "templates", self.tmp / "templates")
        for d in ("notes/concept/statistics", "notes/case", "notes/problem", "notes/qa", "notes/pattern", "maps", "assets", "inbox"):
            (self.tmp / d).mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel: str, text: str):
        p = self.tmp / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def valid_vault(self):
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT)
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE)
        self.write("maps/math-in-biz.md", MAP)

    def run_lint(self) -> lint.Report:
        return lint.run(self.tmp)

    def assert_error(self, rep: lint.Report, fragment: str):
        self.assertFalse(rep.ok, "预期有错误但通过了")
        self.assertTrue(any(fragment in e for e in rep.errors), f"没找到含 {fragment!r} 的错误，实际：{rep.errors}")


class TestValid(VaultCase):
    def test_empty_vault_passes(self):
        rep = self.run_lint()
        self.assertTrue(rep.ok, rep.errors)

    def test_valid_vault_passes(self):
        self.valid_vault()
        rep = self.run_lint()
        self.assertTrue(rep.ok, rep.errors)
        self.assertEqual(rep.stats["concept"], 1)
        self.assertEqual(rep.stats["case"], 1)
        self.assertEqual(rep.stats["map"], 1)
        # map→case（1）+ case→concept（uses + 正文链接，同一目标只算一条）
        self.assertEqual(rep.stats["edges"], 2)

    def test_concept_reachable_via_case_is_not_orphan(self):
        self.valid_vault()
        self.assertTrue(self.run_lint().ok)

    def test_real_repo_passes(self):
        rep = lint.run(REPO)
        self.assertTrue(rep.ok, rep.errors)


class TestFrontmatter(VaultCase):
    def test_missing_frontmatter(self):
        self.valid_vault()
        self.write("notes/concept/statistics/x.md", "# 没有 frontmatter\n")
        self.assert_error(self.run_lint(), "缺少 frontmatter")

    def test_unclosed_frontmatter(self):
        self.valid_vault()
        self.write("notes/concept/statistics/x.md", "---\nid: x\n")
        self.assert_error(self.run_lint(), "没有闭合")

    def test_empty_summary(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("summary: 2×2 列联表小样本下的精确 p 值。", 'summary: ""'))
        self.assert_error(self.run_lint(), "必填字段 `summary` 为空")

    def test_undeclared_field(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("status: stable", "status: stable\nfoo: bar"))
        self.assert_error(self.run_lint(), "未声明的字段 `foo`")

    def test_missing_required_field(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("status: stable\n", ""))
        self.assert_error(self.run_lint(), "缺少必填字段 `status`")

    def test_bad_enum(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("status: stable", "status: done"))
        self.assert_error(self.run_lint(), "取值 `done` 不在")

    def test_updated_before_created(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("updated: 2026-09-07", "updated: 2026-08-01"))
        self.assert_error(self.run_lint(), "早于 created")

    def test_bad_date(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("created: 2026-09-01", "created: 2026/09/01"))
        self.assert_error(self.run_lint(), "不是合法日期")

    def test_block_list_syntax_accepted(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("tags: [statistics, hypothesis-testing]", "tags:\n  - statistics\n  - hypothesis-testing"))
        self.assertTrue(self.run_lint().ok)

    def test_optional_string_may_be_empty(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("aliases: [费舍尔精确检验]", "aliases: []"))
        self.assertTrue(self.run_lint().ok)


class TestIds(VaultCase):
    def test_id_mismatch_filename(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("id: fisher-exact-test", "id: fisher"))
        self.assert_error(self.run_lint(), "与文件名")

    def test_bad_id_format(self):
        self.valid_vault()
        self.write("notes/concept/statistics/Fisher_Test.md", CONCEPT.replace("id: fisher-exact-test", "id: Fisher_Test"))
        self.assert_error(self.run_lint(), "id 不合法")

    def test_duplicate_id_across_dirs(self):
        self.valid_vault()
        dup = CONCEPT.replace("type: concept", "type: qa")
        self.write("notes/qa/fisher-exact-test.md", dup)
        self.assert_error(self.run_lint(), "重复")

    def test_type_mismatch_dir(self):
        self.valid_vault()
        self.write("notes/qa/some-qa.md", CONCEPT.replace("id: fisher-exact-test", "id: some-qa"))
        self.assert_error(self.run_lint(), "与所在目录")


class TestTags(VaultCase):
    def test_unknown_tag(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("tags: [statistics, hypothesis-testing]", "tags: [machine-learning]"))
        self.assert_error(self.run_lint(), "未在 tags.yml 登记")

    def test_empty_tags(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("tags: [statistics, hypothesis-testing]", "tags: []"))
        self.assert_error(self.run_lint(), "至少要 1 项")

    def test_duplicate_tags(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("tags: [statistics, hypothesis-testing]", "tags: [statistics, statistics]"))
        self.assert_error(self.run_lint(), "有重复项")


class TestEdges(VaultCase):
    def test_case_without_uses(self):
        self.valid_vault()
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("uses: [fisher-exact-test]", "uses: []"))
        self.assert_error(self.run_lint(), "`uses` 至少要 1 项")

    def test_uses_unknown_id(self):
        self.valid_vault()
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("uses: [fisher-exact-test]", "uses: [nope]"))
        self.assert_error(self.run_lint(), "引用的 id `nope` 不存在")

    def test_uses_wrong_target_type(self):
        self.valid_vault()
        # 让 case 的 uses 指向另一个 case
        other = CASE.replace("id: ab-test-small-sample-fisher", "id: other-case").replace("uses: [fisher-exact-test]", "uses: [fisher-exact-test]")
        self.write("notes/case/other-case.md", other)
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("uses: [fisher-exact-test]", "uses: [other-case]"))
        self.write("maps/math-in-biz.md", MAP + "- [other](../notes/case/other-case.md)\n")
        self.assert_error(self.run_lint(), "只能指向")

    def test_self_reference(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("related: []", "related: [fisher-exact-test]"))
        self.assert_error(self.run_lint(), "引用了自己")

    def test_ref_written_as_path_rejected(self):
        self.valid_vault()
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("uses: [fisher-exact-test]", "uses: [../concept/statistics/fisher-exact-test.md]"))
        self.assert_error(self.run_lint(), "不是合法 id")


class TestBody(VaultCase):
    def test_broken_link(self):
        self.valid_vault()
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("../concept/statistics/fisher-exact-test.md", "../concept/statistics/nope.md"))
        self.assert_error(self.run_lint(), "链接目标不存在")

    def test_wikilink_rejected(self):
        self.valid_vault()
        self.write("notes/case/ab-test-small-sample-fisher.md", CASE.replace("[Fisher 精确检验](../concept/statistics/fisher-exact-test.md)", "[[fisher-exact-test]]"))
        self.assert_error(self.run_lint(), "wikilink")

    def test_link_inside_code_block_ignored(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n```md\n[x](../nope.md) [[wiki]]\n```\n")
        self.assertTrue(self.run_lint().ok)

    def test_external_links_ignored(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n[wiki](https://en.wikipedia.org/wiki/Fisher%27s_exact_test)\n")
        self.assertTrue(self.run_lint().ok)

    def test_missing_required_heading(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("## 适用边界\n", "## 边界\n"))
        self.assert_error(self.run_lint(), "缺少必需的二级标题 `## 适用边界`")

    def test_leftover_placeholder(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n{{title}}\n")
        self.assert_error(self.run_lint(), "占位符")

    def test_image_outside_assets(self):
        self.valid_vault()
        self.write("notes/concept/statistics/pic.png", "x")  # 也会触发「只放 .md」
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n![p](pic.png)\n")
        self.assert_error(self.run_lint(), "图片必须放在 assets/")

    def test_asset_referenced_and_orphan_asset_warns(self):
        self.valid_vault()
        self.write("assets/fisher-exact-test/table.jpg", "x")
        self.write("assets/fisher-exact-test/unused.jpg", "x")
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n![t](../../../assets/fisher-exact-test/table.jpg)\n")
        rep = self.run_lint()
        self.assertTrue(rep.ok, rep.errors)
        self.assertEqual(len(rep.warnings), 1)
        self.assertIn("unused.jpg", rep.warnings[0])

    def test_asset_file_at_root_rejected(self):
        self.valid_vault()
        self.write("assets/stray.jpg", "x")
        self.assert_error(self.run_lint(), "assets/ 根下不放文件")

    def test_asset_dir_must_match_note_id(self):
        self.valid_vault()
        self.write("assets/no-such-note/x.jpg", "x")
        self.assert_error(self.run_lint(), "不是任何笔记的 id")

    def test_png_asset_rejected(self):
        self.valid_vault()
        self.write("assets/fisher-exact-test/table.png", "x")
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n![t](../../../assets/fisher-exact-test/table.png)\n")
        self.assert_error(self.run_lint(), "不允许 .png 附件")

    def test_unknown_asset_ext_rejected(self):
        self.valid_vault()
        self.write("assets/fisher-exact-test/data.xlsx", "x")
        self.assert_error(self.run_lint(), "不在 schema.json 的 allowed_ext")

    def test_asset_size_warn_and_error(self):
        self.valid_vault()
        (self.tmp / "assets/fisher-exact-test").mkdir(exist_ok=True); (self.tmp / "assets/fisher-exact-test/big.jpg").write_bytes(b"x" * (400 * 1024))
        (self.tmp / "assets/fisher-exact-test/huge.jpg").write_bytes(b"x" * (2 * 1024 * 1024))
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n![a](../../../assets/fisher-exact-test/big.jpg) ![b](../../../assets/fisher-exact-test/huge.jpg)\n")
        rep = self.run_lint()
        self.assertTrue(any("huge.jpg" in e and "超过上限" in e for e in rep.errors), rep.errors)
        self.assertTrue(any("big.jpg" in w and "偏大" in w for w in rep.warnings), rep.warnings)


class TestDomain(VaultCase):
    def test_concept_at_top_level_rejected(self):
        self.valid_vault()
        self.write("notes/concept/loose.md", CONCEPT.replace("id: fisher-exact-test", "id: loose").replace("domain: statistics\n", ""))
        self.assert_error(self.run_lint(), "必须放进领域子目录")

    def test_domain_dir_must_be_registered_tag(self):
        self.valid_vault()
        self.write("notes/concept/nosuch/x.md", CONCEPT.replace("id: fisher-exact-test", "id: x").replace("domain: statistics", "domain: nosuch"))
        self.assert_error(self.run_lint(), "不是 tags.yml 里登记的标签")

    def test_domain_field_must_match_dir(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("domain: statistics", "domain: probability"))
        self.assert_error(self.run_lint(), "与所在目录")

    def test_domain_field_required_in_domain_dir(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("domain: statistics\n", ""))
        self.assert_error(self.run_lint(), "必须写 `domain: statistics`")

    def test_domain_must_be_in_tags(self):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("tags: [statistics, hypothesis-testing]", "tags: [hypothesis-testing]"))
        self.assert_error(self.run_lint(), "必须同时出现在 tags")

    def test_no_nested_domain_dirs(self):
        self.valid_vault()
        self.write("notes/concept/statistics/deeper/x.md", "x")
        self.assert_error(self.run_lint(), "不允许再建子目录")

    def test_case_domain_optional_ok(self):
        self.valid_vault()
        (self.tmp / "notes/case/ab-test-small-sample-fisher.md").unlink()
        self.write("notes/case/ab-test/ab-test-small-sample-fisher.md",
                   CASE.replace("type: case\n", "type: case\ndomain: ab-test\n").replace("../concept/statistics/", "../../concept/statistics/"))
        self.write("maps/math-in-biz.md", MAP.replace("(../notes/case/ab-test-small-sample-fisher.md)", "(../notes/case/ab-test/ab-test-small-sample-fisher.md)"))
        rep = self.run_lint()
        self.assertTrue(rep.ok, rep.errors)

    def test_new_concept_requires_domain(self):
        self.valid_vault()
        with self.assertRaises(new.NewError):
            new.create(self.tmp, "concept", "zzz", "z", tags=["statistics"], today=TODAY)

    def test_new_with_domain_writes_into_subdir_and_adds_tag(self):
        self.valid_vault()
        out = new.create(self.tmp, "concept", "normal-distribution", "正态分布", domain="statistics", map_id="math-in-biz", today=TODAY)
        self.assertEqual(out, self.tmp / "notes/concept/statistics/normal-distribution.md")
        text = out.read_text()
        self.assertIn("domain: statistics", text)
        self.assertIn("tags: [statistics]", text)


class TestMath(VaultCase):
    def body(self, extra):
        self.valid_vault()
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT + "\n" + extra + "\n")
        return self.run_lint()

    def test_unicode_math_in_prose_rejected(self):
        self.assert_error(self.body("统计量 χ² ≥ 5 才行。"), "数学符号要写成 LaTeX")

    def test_latex_inline_ok(self):
        rep = self.body("统计量 $\\chi^2 \\ge 5$ 才行，$2\\times 2$ 表。")
        self.assertTrue(rep.ok, rep.errors)

    def test_unicode_inside_math_or_code_ignored(self):
        rep = self.body("公式 $χ^2$ 和代码 `χ²` 都不管。")
        self.assertTrue(rep.ok, rep.errors)

    def test_unpaired_dollar(self):
        self.assert_error(self.body("只有一个 $ 符号。"), "不配对")

    def test_escaped_dollar_ok(self):
        self.assertTrue(self.body("价格 \\$5。").ok)

    def test_space_inside_inline_math(self):
        self.assert_error(self.body("写成 $ p = 0.03 $ 不行。"), "内侧不能有空格")

    def test_double_dollar_inline_rejected(self):
        self.assert_error(self.body("行内 $$x$$ 不行。"), "单独占一行")

    def test_block_needs_blank_lines(self):
        self.assert_error(self.body("前一行\n$$\nx=1\n$$\n后一行"), "前面要空一行")
        self.assert_error(self.body("\n$$\nx=1\n$$\n后一行"), "后面要空一行")

    def test_block_no_blank_inside(self):
        self.assert_error(self.body("\n$$\nx=1\n\ny=2\n$$\n"), "不能有空行")

    def test_block_unclosed(self):
        self.assert_error(self.body("\n$$\nx=1\n"), "没有闭合")

    def test_block_ok(self):
        rep = self.body("\n$$\nP(A=a)=\\frac{\\binom{r_1}{a}}{\\binom{n}{c_1}}\n$$\n")
        self.assertTrue(rep.ok, rep.errors)

    def test_bad_delimiters(self):
        self.assert_error(self.body("用 \\(x\\) 不行。"), "定界符")

    def test_math_in_heading_rejected(self):
        self.assert_error(self.body("## 关于 $x$ 的一节"), "标题里不放公式")

    def test_map_arrow_annotation_ok(self):
        self.valid_vault()
        self.write("maps/math-in-biz.md", MAP + "- [x](../notes/concept/statistics/fisher-exact-test.md) ← 先看这个\n")
        self.assertTrue(self.run_lint().ok)


class TestMaps(VaultCase):
    def test_map_prose_line_rejected(self):
        self.valid_vault()
        self.write("maps/math-in-biz.md", MAP + "\n这是一段正文，不该出现在索引页。\n")
        self.assert_error(self.run_lint(), "索引页每一行都必须是链接")

    def test_map_heading_and_comment_allowed(self):
        self.valid_vault()
        self.write("maps/math-in-biz.md", MAP + "\n## 另一组\n<!-- 待补 -->\n")
        self.assertTrue(self.run_lint().ok)

    def test_map_link_to_other_map_counts(self):
        self.valid_vault()
        self.write("maps/interview.md", MAP.replace("id: math-in-biz", "id: interview").replace("- [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md) ← 先看这个", "- [业务 × 原理](math-in-biz.md)"))
        self.assertTrue(self.run_lint().ok)


class TestReachability(VaultCase):
    def test_orphan_note(self):
        self.valid_vault()
        self.write("notes/concept/statistics/lonely.md", CONCEPT.replace("id: fisher-exact-test", "id: lonely"))
        self.assert_error(self.run_lint(), "孤儿")

    def test_note_reachable_only_via_related(self):
        self.valid_vault()
        self.write("notes/concept/statistics/chi-square-test.md", CONCEPT.replace("id: fisher-exact-test", "id: chi-square-test"))
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT.replace("related: []", "related: [chi-square-test]"))
        self.assertTrue(self.run_lint().ok)

    def test_no_maps_means_all_orphans(self):
        self.write("notes/concept/statistics/fisher-exact-test.md", CONCEPT)
        self.assert_error(self.run_lint(), "孤儿")


class TestStructure(VaultCase):
    def test_undeclared_type_dir(self):
        self.valid_vault()
        (self.tmp / "notes/essay").mkdir()
        self.assert_error(self.run_lint(), "未声明的目录")

    def test_subdir_in_type_without_domains(self):
        self.valid_vault()
        (self.tmp / "maps/sub").mkdir()
        self.assert_error(self.run_lint(), "不允许领域子目录")

    def test_file_at_notes_root(self):
        self.valid_vault()
        self.write("notes/stray.md", CONCEPT)
        self.assert_error(self.run_lint(), "notes/ 根下不允许放文件")

    def test_readme_exempt(self):
        self.valid_vault()
        self.write("notes/concept/README.md", "# 说明\n")
        self.assertTrue(self.run_lint().ok)

    def test_inbox_counted_not_linted(self):
        self.valid_vault()
        self.write("inbox/2026-09-07-scrap.md", "随便写")
        rep = self.run_lint()
        self.assertTrue(rep.ok)
        self.assertEqual(rep.stats["inbox"], 1)


class TestNew(VaultCase):
    def test_every_template_generates_lintable_note(self):
        """每种类型的模板生成后，只填 summary/tags/必填边就能过 lint（模板与 schema 对齐的证据）。"""
        self.write("maps/home.md", MAP.replace("id: math-in-biz", "id: home").replace("- [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md) ← 先看这个", "<!-- 空 -->"))
        schema = lint.load_schema(self.tmp, lint.Report())
        for t in schema["types"]:
            if t == "map":
                continue
            p = new.create(self.tmp, t, f"sample-{t}", f"示例 {t}", tags=["statistics"], map_id="home", today=TODAY,
                           domain="statistics" if t == "concept" else None)
            text = p.read_text(encoding="utf-8").replace('summary: ""', "summary: 一句话。")
            if t == "case":
                text = text.replace("uses: []", "uses: [sample-concept]")
            p.write_text(text, encoding="utf-8")
        rep = self.run_lint()
        self.assertTrue(rep.ok, rep.errors)
        self.assertEqual(rep.stats["edges"], 6)  # home→5 篇 + case→concept

    def test_map_template_generates_lintable_map(self):
        p = new.create(self.tmp, "map", "interview", "面试准备", today=TODAY)
        p.write_text(p.read_text(encoding="utf-8").replace('summary: ""', "summary: 面试。"), encoding="utf-8")
        self.assertTrue(self.run_lint().ok)

    def test_new_without_summary_fails_lint(self):
        self.write("maps/home.md", MAP.replace("id: math-in-biz", "id: home").replace("- [小样本 AB 用 Fisher 判显著](../notes/case/ab-test-small-sample-fisher.md) ← 先看这个", "<!-- 空 -->"))
        new.create(self.tmp, "concept", "x", "X", tags=["statistics"], map_id="home", today=TODAY, domain="statistics")
        self.assert_error(self.run_lint(), "必填字段 `summary` 为空")

    def test_new_attaches_to_map_unsorted_section(self):
        new.create(self.tmp, "map", "home", "首页", today=TODAY)
        new.create(self.tmp, "concept", "x", "X 原理", tags=["statistics"], map_id="home", today=TODAY, domain="statistics")
        text = (self.tmp / "maps/home.md").read_text(encoding="utf-8")
        self.assertIn("## 未归类\n- [X 原理](../notes/concept/statistics/x.md)", text)
        self.assertIn(f"updated: {TODAY}", text)

    def test_new_attach_appends_within_unsorted_before_next_heading(self):
        new.create(self.tmp, "map", "home", "首页", today=TODAY)
        home = self.tmp / "maps/home.md"
        home.write_text(home.read_text(encoding="utf-8") + "\n## 其他\n<!-- x -->\n", encoding="utf-8")
        new.create(self.tmp, "concept", "a", "A", tags=["statistics"], map_id="home", today=TODAY, domain="statistics")
        new.create(self.tmp, "concept", "b", "B", tags=["statistics"], map_id="home", today=TODAY, domain="statistics")
        text = home.read_text(encoding="utf-8")
        self.assertIn("## 未归类\n- [A](../notes/concept/statistics/a.md)\n- [B](../notes/concept/statistics/b.md)\n\n## 其他", text)

    def test_new_rejects_duplicate_id(self):
        new.create(self.tmp, "concept", "x", "X", today=TODAY, domain="statistics")
        with self.assertRaises(new.NewError):
            new.create(self.tmp, "qa", "x", "X again", today=TODAY)

    def test_new_rejects_bad_id_and_type(self):
        with self.assertRaises(new.NewError):
            new.create(self.tmp, "concept", "Bad_Id", "X", today=TODAY)
        with self.assertRaises(new.NewError):
            new.create(self.tmp, "essay", "x", "X", today=TODAY)

    def test_new_rejects_missing_map(self):
        with self.assertRaises(new.NewError):
            new.create(self.tmp, "concept", "x", "X", map_id="nope", today=TODAY)


if __name__ == "__main__":
    unittest.main()
