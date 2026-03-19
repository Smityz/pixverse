"""Pipeline stage 5: Submit shots to Pixverse and download video clips."""

import json
from pathlib import Path

import httpx
from pixverse import PixverseError

from .common import pixverse as pixverse_client, log, safe_filename


def run(script: dict, out_dir: Path) -> None:
    jobs_file = out_dir / "jobs.json"

    if jobs_file.exists():
        jobs = [tuple(j) for j in json.loads(jobs_file.read_text(encoding="utf-8"))]
        log(f"resume: 加载已有任务 jobs.json ({len(jobs)}个)")
    else:
        print("\n🚀 提交视频生成任务…\n")
        jobs = []
        for si, scene in enumerate(script["scenes"], 1):
            for sj, shot in enumerate(scene["shots"], 1):
                try:
                    vid = pixverse_client.generate(
                        shot["prompt"],
                        model="v4.5",
                        quality="360p",
                        duration=5,
                    )
                    print(f"  ✓ {si:02d}-{sj} 「{scene['title']}」{shot['desc']} video_id={vid}")
                    jobs.append((si, sj, scene["title"], shot["desc"], vid))
                except PixverseError as e:
                    print(f"  ✗ {si:02d}-{sj} 「{scene['title']}」{shot['desc']} 提交失败：{e}")

        jobs_file.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"step5: Pixverse 提交完毕 ({len(jobs)}个任务)")

    if not jobs:
        print("\n没有成功提交的视频任务。")
        return

    print("\n⏳ 等待生成并下载…\n")
    for si, sj, scene_title, shot_desc, vid in jobs:
        fname = out_dir / f"{si:02d}_{safe_filename(scene_title)}_shot{sj:02d}.mp4"
        if fname.exists():
            print(f"  ✅ 已有 {fname.name}，跳过")
            continue
        try:
            url = pixverse_client.wait(vid)
            print(f"  🎥 {si:02d}-{sj} {scene_title} · {shot_desc}\n     {url}")
            with httpx.stream("GET", url, timeout=300) as r:
                r.raise_for_status()
                with open(fname, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=65536):
                        f.write(chunk)
            log(f"step5: 下载完成 {fname.name}")
            print(f"     已保存 → {fname}\n")
        except (PixverseError, TimeoutError) as e:
            log(f"step5: 下载失败 {si:02d}-{sj} {scene_title} — {e}")
            print(f"  ✗ {si:02d}-{sj} {scene_title} 失败：{e}\n")
