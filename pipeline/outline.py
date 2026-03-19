"""Pipeline stage 1: Generate story outline from theme."""

from pathlib import Path

from .common import chat, log


def run(theme: str, out_dir: Path) -> str:
    cached = out_dir / "outline.txt"
    if cached.exists():
        log("outline: 已有 outline.txt，跳过生成")
        return cached.read_text(encoding="utf-8")

    outline = chat(
        system=(
            "你是一位专业的短剧编剧。根据用户给出的主题，创作一个完整的短剧故事大纲，包含：\n"
            "- 剧名\n"
            "- 主要人物（2-3人）及其关系\n"
            "- 故事背景\n"
            "- 完整情节：开端 → 发展 → 高潮 → 结局\n"
            "用中文写作，语言生动，情节有冲突感和戏剧张力。大纲约300字。"
        ),
        user=f"主题：{theme}",
        label="step1 大纲",
    )
    print("\n" + "─" * 60)
    print(outline)
    print("─" * 60)
    cached.write_text(outline, encoding="utf-8")
    log("step1: 大纲生成完毕")
    return outline
