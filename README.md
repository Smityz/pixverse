# AI 短剧生成器

用 LLM 生成剧本，再驱动 Pixverse 逐场景生成视频片段的端到端 demo。

## 项目结构

```
├── demo.py          主程序
├── pixverse.py      Pixverse SDK 封装
├── scripts/         工具脚本（余额查询、接口冒烟测试）
├── docs/api.md      Pixverse API 参考
└── output/          生成内容（gitignore）
```

## 快速开始

配置 `.env`：

```
PIXVERSE_API_KEY=...
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api-inference.modelscope.cn/v1
OPENAI_MODEL=Qwen/Qwen3.5-27B
```

运行：

```bash
uv run demo.py
```

## 进度日志

### 2026-03-19 18:54 — 初版 Demo 可用

- 接入 Pixverse SDK（`pixverse.py`），封装 text-to-video 生成与轮询
- 接入 Qwen（via ModelScope OpenAI-compatible API）
- 链路：用户输入主题 → Qwen 生成故事大纲 → Qwen 拆分5个场景 prompt → Pixverse 逐场景生成视频 → 下载保存
- 输出按 `output/时间戳_剧名/` 目录归档，包含 `outline.txt`、`script.json`、`01~05_*.mp4`

**TODO**
- [ ] 角色一致性：跨场景保持主要人物外貌一致
- [ ] 字幕：为每个片段添加对白/旁白字幕，辅助交代剧情

### 2026-03-19 19:08 — 角色一致性（角色外貌标签卡）

- 在大纲生成与场景拆分之间新增步骤 2.5：Qwen 从大纲中提取每位主要角色的固定英文外貌描述（性别、年龄、发型、肤色、服装、标志性特征，约30词）
- 外貌描述以"角色标签卡"形式注入场景 prompt 生成的 system prompt，并要求逐字嵌入每个相关场景的 prompt
- Pixverse 每次渲染都拿到相同的视觉锚点，同一角色跨场景服装/发型/妆容一致
- 输出目录新增 `characters.json` 保存角色描述，便于复盘
- 测试用例：《双生劫》（姐妹创业背叛悬疑），5个场景全部生成下载成功

**TODO**
- [ ] 字幕：为每个片段添加对白/旁白字幕，辅助交代剧情
- [ ] 情节展开：单个场景拆分为多个连续镜头，完整讲述一段情节