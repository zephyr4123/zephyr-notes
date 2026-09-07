"""出图公共设置：中文字体、统一尺寸、只存 JPEG。

用法（在 tools/figures/<note-id>.py 里）：
    from _style import plt, save_jpeg, ASSETS
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ...
    save_jpeg(fig, "fisher-exact-test", "pmf")   # -> assets/fisher-exact-test/pmf.jpg
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)  # Hiragino 只有 W3/W6，权重回退提示无意义
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402  matplotlib 自带 pillow 依赖

ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS = ROOT / "assets"

# 中文字体：macOS 自带 Hiragino Sans GB；找不到时退到 Arial Unicode MS / 默认字体（会有豆腐块，出图后肉眼看一眼）
plt.rcParams.update({
    "font.family": ["Hiragino Sans GB", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "legend.fontsize": 10,
    "figure.dpi": 100,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
})

# 一套克制的配色：对照 / 试验 / 强调 / 灰
C_A = "#4C72B0"      # 对照
C_B = "#DD8452"      # 试验
C_HI = "#C44E52"     # 强调 / 观测值
C_GRAY = "#8C8C8C"


def save_jpeg(fig, note_id: str, desc: str, *, max_width: int = 1600, quality: int = 85, dpi: int = 200) -> Path:
    """把 fig 存成 assets/<note_id>/<desc>.jpg：白底、宽度 ≤ max_width px、JPEG 质量 quality。返回路径并打印大小。"""
    if "." in desc or "/" in desc or "/" in note_id:
        raise ValueError("note_id 是笔记 id，desc 不带后缀和路径")
    out_dir = ASSETS / note_id
    out_dir.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    if img.width > max_width:
        h = round(img.height * max_width / img.width)
        img = img.resize((max_width, h), Image.LANCZOS)
    out = out_dir / f"{desc}.jpg"
    img.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    plt.close(fig)
    print(f"✓ {out.relative_to(ROOT)}  {img.width}×{img.height}  {out.stat().st_size // 1024} KB", file=sys.stderr)
    return out
