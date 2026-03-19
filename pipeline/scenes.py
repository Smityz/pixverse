"""Pipeline stage 3: Split outline into 5 scenes."""

import json
from pathlib import Path

from .common import chat, log


def run(outline: str, out_dir: Path) -> dict:
    cached = out_dir / "script.json"
    if cached.exists():
        log("scenes: 已有 script.json，跳过生成")
        return json.loads(cached.read_text(encoding="utf-8"))

    scenes_json = chat(
        system=(
            "你是一位视频导演。根据提供的故事大纲，将其拆分为5个关键场景。\n"
            "输出 ONLY 合法 JSON，格式如下（不要 markdown 代码块）：\n"
            '{"title": "剧名", "scenes": [\n'
            '  {"title": "场景中文标题", "summary": "该场景情节的中文简述，约30字"}\n'
            "]}\n"
            "要求：\n"
            "- 恰好5个场景，按故事顺序排列\n"
            "- summary 用中文，简明描述本场景发生了什么"
        ),
        user=f"故事大纲：\n{outline}",
        json_mode=True,
        label="step3 场景",
    )
    script = json.loads(scenes_json)
    cached.write_text(
        json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"step3: 场景拆分完毕 ({len(script['scenes'])}个场景)")
    return script
