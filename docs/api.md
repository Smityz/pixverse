# Pixverse Platform API

**Base URL:** `https://app-api.pixverse.ai`
**Docs:** https://docs.platform.pixverse.ai/

---

## 认证

每个请求必须携带以下 Header：

| Header | 说明 |
|---|---|
| `API-KEY` | 在 https://platform.pixverse.ai/ → API Keys 创建，**只显示一次，请立即保存** |
| `Ai-trace-id` | 每次请求必须生成新的 UUID，**不可复用**（复用会导致生成静默失败） |

---

## 工作流程（异步）

1. 提交生成请求 → 获得 `video_id`
2. 每隔 3–5 秒轮询状态接口
3. `status == 1` 时，通过返回的 URL 下载视频

---

## 接口列表

### 1. 文生视频

**POST** `/openapi/v2/video/text/generate`

Headers: `API-KEY`, `Ai-trace-id`, `Content-Type: application/json`

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `prompt` | 是 | string | 最多 2048 字符 |
| `model` | 是 | string | `"v3.5"` / `"v4"` / `"v4.5"` |
| `aspect_ratio` | 是 | string | `"16:9"` / `"9:16"` / `"1:1"` / `"3:4"` / `"4:3"` |
| `duration` | 是 | integer | `5` 或 `8`（1080p 仅支持 5） |
| `quality` | 是 | string | `"360p"` / `"540p"` / `"720p"` / `"1080p"` |
| `negative_prompt` | 否 | string | 最多 2048 字符 |
| `motion_mode` | 否 | string | `"normal"`（默认）/ `"fast"`（仅 5s，不兼容 1080p） |
| `camera_movement` | 否 | string | `"zoom_in"` / `"pan_left"` / `"hitchcock"` 等约 18 种 |
| `style` | 否 | string | `"anime"` / `"3d_animation"` / `"day"` / `"cyberpunk"` / `"comic"` |
| `seed` | 否 | integer | 0–2147483647 |
| `template_id` | 否 | integer | 特效模板 ID（需先在 Effect Center 激活） |

**Response:**
```json
{ "ErrCode": 0, "ErrMsg": "string", "Resp": { "video_id": 0 } }
```

---

### 2. 图片上传（图生视频的前置步骤）

**POST** `/openapi/v2/image/upload`

Headers: `API-KEY`, `Ai-trace-id`

Body: `multipart/form-data`，字段名 `image`

限制：JPG / PNG / WebP，最大 20MB，最大 4000×4000px

**Response:**
```json
{ "ErrCode": 0, "Resp": { "img_id": 123, "img_url": "https://..." } }
```

---

### 3. 图生视频 / 特效

**POST** `/openapi/v2/video/img/generate`

Headers: `API-KEY`, `Ai-trace-id`, `Content-Type: application/json`

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `img_id` | 是* | integer | 单张图片的 img_id |
| `img_ids` | 是* | integer[] | 多图特效时使用（替代 `img_id`） |
| `prompt` | 是 | string | 最多 2048 字符 |
| `model` | 是 | string | `"v3.5"` / `"v4"` / `"v4.5"` |
| `duration` | 是 | integer | `5` 或 `8` |
| `quality` | 是 | string | `"360p"` / `"540p"` / `"720p"` / `"1080p"` |
| `negative_prompt` | 否 | string | 最多 2048 字符 |
| `motion_mode` | 否 | string | `"normal"` / `"fast"` |
| `camera_movement` | 否 | string | 方向/特效选项 |
| `style` | 否 | string | 风格选项 |
| `seed` | 否 | integer | 0–2147483647 |
| `template_id` | 否 | integer | 特效模板 ID |

**Response:** 与文生视频相同（返回 `video_id`）

**多图特效示例:**
```json
{
  "duration": 5,
  "img_ids": [123, 456],
  "model": "v4.5",
  "motion_mode": "normal",
  "prompt": "Muscle Surge",
  "quality": "540p",
  "seed": 0,
  "template_id": 308621408717184
}
```

---

### 4. 首尾帧过渡（Transition）

**POST** `/openapi/v2/video/transition/generate`

Headers: `API-KEY`, `Ai-trace-id`, `Content-Type: application/json`

| 参数 | 必填 | 类型 | 说明 |
|---|---|---|---|
| `first_frame_img` | 是 | integer | 起始帧的 img_id |
| `last_frame_img` | 是 | integer | 结束帧的 img_id |
| `prompt` | 是 | string | 最多 2048 字符 |
| `model` | 是 | string | `"v3.5"` / `"v4"` / `"v4.5"` |
| `duration` | 是 | integer | `5` 或 `8` |
| `quality` | 是 | string | `"360p"` / `"540p"` / `"720p"` / `"1080p"` |
| `motion_mode` | 否 | string | `"normal"` / `"fast"` |
| `seed` | 否 | integer | 0–2147483647 |
| `negative_prompt` | 否 | string | 最多 2048 字符 |

**Response:** 返回 `video_id`

---

### 5. 口型同步（Lip Sync）

视频来源（二选一）：`source_video_id` 或 `video_media_id`

音频来源（二选一）：
- `audio_media_id`
- `lip_sync_tts_speaker_id` + `lip_sync_tts_content`（约 200 字符，非 UTF-8 编码）

---

### 6. 视频延长（Extend）

结合文生视频与 Transition 的参数，支持灵活的视频来源输入。

---

### 7. 查询视频状态

**GET** `/openapi/v2/video/result/{video_id}`

Headers: `API-KEY`, `Ai-trace-id`

**Response:**
```json
{
  "ErrCode": 0,
  "ErrMsg": "success",
  "Resp": {
    "id": 0,
    "status": 1,
    "url": "https://...",
    "prompt": "...",
    "negative_prompt": "...",
    "style": "...",
    "outputWidth": 1920,
    "outputHeight": 1080,
    "create_time": "...",
    "modify_time": "...",
    "seed": 0,
    "size": 0
  }
}
```

**Status 状态码：**

| 值 | 含义 |
|---|---|
| `1` | 生成成功 |
| `5` | 生成中（继续轮询，建议间隔 3–5s） |
| `7` | 内容审核未通过 |
| `8` | 生成失败 |

---

### 8. 账户余额查询

**GET** `/openapi/v2/account/balance`

Headers: `API-KEY`, `Ai-trace-id`

**Response:**
```json
{
  "ErrCode": 0,
  "ErrMsg": "success",
  "Resp": {
    "account_id": 0,
    "credit_monthly": 1069020,
    "credit_package": 3630
  }
}
```

| 字段 | 说明 |
|---|---|
| `credit_monthly` | 订阅套餐每月积分（每月重置） |
| `credit_package` | 购买积分包的余额 |

---

## 接口汇总

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/openapi/v2/video/text/generate` | 文生视频 |
| POST | `/openapi/v2/image/upload` | 上传图片 |
| POST | `/openapi/v2/video/img/generate` | 图生视频 / 特效 |
| POST | `/openapi/v2/video/transition/generate` | 首尾帧过渡 |
| GET | `/openapi/v2/video/result/{video_id}` | 查询生成状态 |
| GET | `/openapi/v2/account/balance` | 查询积分余额 |

---

## 套餐与计费

| 套餐 | 价格 | 月积分 | 约 5s 视频数 | 并发数 | 最高分辨率 | 额外功能 |
|---|---|---|---|---|---|---|
| Free | $0 | 测试积分 | — | 1 | 540P | Transition |
| Essential | $100/月 | 15,000 | ~333 | 5 | 1080P | + Lip Sync, Extend |
| Scale | $1,500/月 | 239,230 | ~5,316 | 10 | 1080P | + Lip Sync, Extend |
| Business | $6,000/月 | 1,069,500 | ~23,766 | 15 | 1080P | + Lip Sync, Extend |

**积分消耗参考（V3.5 模型）：**
- 360P Turbo, 5s：45 积分
- 1080P, 5s normal：120 积分
- 1080P, 5s fast：120 积分

> **注意：** API 会员与网页端（app.pixverse.ai）会员独立，积分不互通。

---

## 限速说明

- 并发数上限按套餐tier限制（1–15 个并行任务）
- 任务超过 10 分钟未完成，自动释放并发槽
- 以下情况退还积分：生成失败、2 小时超时、内容审核失败
- 超过 10 分钟的超时释放并发槽，但**不退还积分**

---

## 错误码

| 错误码 | 含义 |
|---|---|
| `0` | 成功 |
| `400011` | 参数为空 |
| `400012` | 账户无效 |
| `400013` | 参数类型/值错误 |
| `400017` | 参数无效 |
| `400018/400019` | prompt/negative_prompt 超过 2048 字符 |
| `400032` | 图片 ID 无效 |
| `500008` | 请求数据未找到 |
| `500020` | 无操作权限 |
| `500030` | 图片超过 20MB 或 4000×4000px |
| `500031` | 获取图片信息失败 |
| `500032` | 图片格式无效 |
| `500033` | 图片宽高无效 |
| `500041` | 图片上传失败 |
| `500042` | 图片路径无效 |
| `500044` | 已达并发生成上限 |
| `500054` | 图片内容审核失败 |
| `500060` | 月度激活配额已耗尽 |
| `500063` | 内容审核失败（视频/图片/文本） |
| `500064` | 内容已被删除 |
| `500069` | 系统过载，请重试 |
| `500070` | 模板未激活 |
| `500071` | 该特效不支持 720p/1080p |
| `500090` | 积分不足 |
| `500100` | 数据库错误 |
| `99999` | 未知错误 |

---

## 联系支持

- **邮件：** api@pixverse.ai（请提供：账户 ID、邮箱、问题类型、描述、相关 `Ai-trace-id`）
- **Discord：** https://discord.gg/pDKeNnZk
- **企业合作：** api_business@pixverse.ai
