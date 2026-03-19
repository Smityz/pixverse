"""Pipeline stage 4: Expand each scene into 3 shots (parallel, with incremental checkpoints)."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .common import chat, log


def _expand_scene(scene: dict, outline: str, char_ref: str) -> dict:
    shots_json = chat(
        system=(
            "你是一位影视分镜导演。将给定的剧情场景拆分为 3 个连续镜头（shot），"
            "每个镜头约 5 秒，合在一起完整讲述这段情节。\n"
            "输出 ONLY 合法 JSON，格式如下（不要 markdown 代码块）：\n"
            '{"shots": [\n'
            '  {"desc": "镜头中文描述（15字内）", "prompt": "cinematic English video prompt"}\n'
            "]}\n"
            "要求：\n"
            "- 3 个镜头按时间顺序，形成起承转的节奏\n"
            "- 每个 prompt 必须嵌入该镜头出现角色的完整外貌描述（直接嵌入文本）\n"
            "- prompt 描述：镜头类型、环境、角色动作、表情、光线氛围，约 60 词\n"
            "- prompt 必须是英文\n\n"
            f"固定角色外貌：\n{char_ref}"
        ),
        user=(
            f"场景标题：{scene['title']}\n"
            f"场景情节：{scene['summary']}\n\n"
            f"故事大纲（用于理解整体情节）：\n{outline}"
        ),
        json_mode=True,
        label=f"step4 分镜[{scene['title']}]",
    )
    raw_shots = json.loads(shots_json)["shots"]
    scene["shots"] = [
        {
            "desc": s.get("desc") or s.get("description") or s.get("title") or "",
            "prompt": s.get("prompt") or s.get("content") or "",
        }
        for s in raw_shots
    ]
    return scene


def run(script: dict, outline: str, char_ref: str, out_dir: Path) -> dict:
    shots_file = out_dir / "shots.json"

    if shots_file.exists():
        script = json.loads(shots_file.read_text(encoding="utf-8"))
        done = sum(1 for s in script["scenes"] if s.get("shots"))
        log(f"resume: 加载已有分镜 shots.json ({done}/{len(script['scenes'])}个场景已完成)")

    pending = [s for s in script["scenes"] if not s.get("shots")]

    if not pending:
        total = sum(len(s["shots"]) for s in script["scenes"])
        log(f"step4: 分镜已全部完成 ({total}个镜头)，跳过")
        return script

    print(f"\n⏳ 展开分镜（{len(pending)}个场景并行→各3个镜头）…\n")

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(_expand_scene, scene, outline, char_ref): scene for scene in pending}
        for fut in as_completed(futures):
            scene = fut.result()
            print(f"  ✓ {scene['title']}")
            for j, shot in enumerate(scene["shots"], 1):
                print(f"     Shot {j}：{shot['desc']}")
            shots_file.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"step4 checkpoint: {scene['title']} 已保存")

    total_shots = sum(len(s["shots"]) for s in script["scenes"])
    log(f"step4: 分镜展开完毕 ({total_shots}个镜头)")
    return script
