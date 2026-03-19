"""端到端演示：主题 → 大纲 → 角色 → 场景 → 分镜 → 视频

Usage:
  uv run demo.py                        # fresh run
  uv run demo.py output/20260319_xxx    # resume from checkpoint
"""

import sys
from datetime import datetime
from pathlib import Path

from pipeline.common import set_log_path
from pipeline import outline, characters, scenes, shots, video

# ── config ────────────────────────────────────────────────────────────────────
theme = "一个关于姐妹情谊与背叛的悬疑短剧：两姐妹共同创业，却因一份遗嘱反目成仇"

# ── 输出目录 ──────────────────────────────────────────────────────────────────
resume_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None

if resume_path:
    out_dir = resume_path
else:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path("output") / ts
    out_dir.mkdir(parents=True)

set_log_path(out_dir / "run.log")

# ── 剧本生成 ──────────────────────────────────────────────────────────────────
outline_text = outline.run(theme, out_dir)
chars = characters.run(outline_text, out_dir)
script = scenes.run(outline_text, out_dir)

# ── 分镜展开 ──────────────────────────────────────────────────────────────────
char_ref = "\n".join(f"- {c['name']}: {c['visual']}" for c in chars)

print(f"\n🎬 《{script['title']}》— 场景列表\n")
for i, scene in enumerate(script["scenes"], 1):
    print(f"  {i}. {scene['title']}：{scene.get('summary', '')}")

script = shots.run(script, outline_text, char_ref, out_dir)

# ── 视频生成 ──────────────────────────────────────────────────────────────────
video.run(script, out_dir)
