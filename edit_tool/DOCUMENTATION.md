# edit_tool 使用说明文档

`edit_tool` 是一个 Python 剪辑工具，调用**火山引擎 AI MediaKit** 的
**视频拼接（concat-video）** 能力：传入两个及以上视频（或图片），接口按顺序拼接，
并可在拼接处添加**转场效果**，最终返回一个 MP4 成片。

- 拼接任务为**异步**：先创建任务拿到 `task_id`，再轮询任务直到完成。
- 输入支持**公网 URL**，也支持**本地文件**（工具会先上传到文件托管服务换取公网 URL）。
- 不传转场时，接口默认是**硬切**（没有转场）。

---

## 1. 目录结构

```text
edit_tool/
├── concat_video.py        # 主程序（库 + 命令行）
├── config.json            # 你的真实配置（含 API Key，已被 .gitignore 忽略，不会上传）
├── config.example.json    # 配置模板（会上传到 GitHub）
├── requirements.txt       # 依赖
├── README.md              # 快速开始
├── DOCUMENTATION.md       # 本文档
├── test_input/            # 示例输入视频
└── output/                # 输出结果（.mp4 已被 .gitignore 忽略）
```

---

## 2. 安装

需要 Python 3.8+。

```bash
cd edit_tool
pip install -r requirements.txt
```

依赖只有 `requests`。

---

## 3. 配置（重点）

### 3.1 创建配置文件

复制模板为 `config.json`：

```bash
cd edit_tool
cp config.example.json config.json
```

> `config.json` 含密钥，已加入仓库根目录 `.gitignore`（规则 `edit_tool/config.json`），
> **不会被上传到 GitHub**；仓库只提交 `config.example.json` 模板。

### 3.2 配置 API Key

在 `config.json` 中把 `api_key` 换成你自己的火山引擎 AI MediaKit API Key：

```json
{
  "api_key": "你的火山引擎 MediaKit API Key",
  "base_url": "https://mediakit.cn-beijing.volces.com",
  "project": "default"
}
```

- `api_key`：**必填**。格式形如 `VxCg...xG7T...`，在火山引擎 AI MediaKit 控制台获取。
- `base_url`：接口域名，默认 `https://mediakit.cn-beijing.volces.com`。
- 程序使用 `Authorization: Bearer <api_key>` 请求头鉴权。

### 3.3 全部配置项

| 字段 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `api_key` | string | 是 | - | 火山引擎 MediaKit API Key |
| `base_url` | string | 否 | `https://mediakit.cn-beijing.volces.com` | 接口域名 |
| `project` | string | 否 | `default` | 项目名，对应请求体的 `Project` |
| `transitions` | array<string> | 否 | `[]` | 默认转场（名称/别名/ID），命令行 `--transition` 可覆盖 |
| `timeout_seconds` | number | 否 | `120` | 单次 HTTP 请求超时（秒），也用于上传超时 |
| `poll_interval_seconds` | number | 否 | `5` | 轮询任务状态的间隔（秒） |
| `poll_timeout_seconds` | number | 否 | `600` | 轮询总超时（秒） |
| `uploader` | object | 否 | 见下 | 本地文件上传配置 |

### 3.4 上传器（uploader）配置

拼接接口只接受**公网 URL**。当输入是本地文件时，工具会先用 `uploader` 把它上传，换取公网 URL。

默认使用 `uguu.se`（返回直链，火山引擎可正常拉取）：

```json
{
  "uploader": {
    "enabled": true,
    "url": "https://uguu.se/upload.php",
    "file_field": "files[]",
    "extra_fields": {},
    "response_path": "files.0.url"
  }
}
```

| 字段 | 说明 |
| --- | --- |
| `enabled` | 是否启用本地文件自动上传；`false` 时只接受 URL |
| `url` | 上传接口地址 |
| `file_field` | multipart 文件字段名，如 `files[]`、`file`、`fileToUpload` |
| `extra_fields` | 额外表单字段（键值对） |
| `response_path` | 从 JSON 响应按点路径取 URL，如 `files.0.url`、`data.url` |
| `url_replace` | 可选，对取到的 URL 做前缀替换，如 `["旧前缀", "新前缀"]` |

> 注意：并非所有托管服务的直链都能被火山引擎拉取。
> 例如 **catbox** 的 HEAD 返回 `Content-Length: 0`、**tmpfiles** 的直链会 302 跳转，
> 都会被判定为不可用而任务失败。请使用能返回**直接可下载直链**的服务。
> 生产环境建议使用火山引擎 **TOS / VOD**（接口支持 `tos://`、`vod://` 输入）。

---

## 4. 命令行调用

### 4.1 基本格式

```bash
python concat_video.py <输入1> <输入2> [输入3 ...] [选项]
```

- 输入可以是：公网 `http(s)` URL，或本地视频/图片文件路径。
- 至少需要 **2 个**输入。
- 程序把**成片 URL** 打印到 **stdout**；上传/轮询进度打印到 **stderr**。

### 4.2 全部选项

| 选项 | 说明 |
| --- | --- |
| `inputs`（位置参数） | 两个及以上素材：URL 或本地文件路径 |
| `--config PATH` | 配置文件路径，默认 `edit_tool/config.json` |
| `--project NAME` | 覆盖配置中的 `Project` |
| `--transition VALUE` | 指定转场，可多次或用逗号分隔；支持中文名/英文别名/ID |
| `--no-transition` | 强制硬切，不添加转场 |
| `--list-transitions` | 列出全部可用转场后退出 |
| `--output PATH` | 把成片下载到本地路径 |
| `--param key=value` | 透传额外请求参数，可多次（值会尝试按 JSON 解析） |
| `--no-upload` | 禁止自动上传本地文件（只接受 URL） |
| `--quiet` | 不输出轮询/上传进度 |

### 4.3 调用示例

```bash
# 1) 传入两个公网 URL，打印成片地址
python concat_video.py \
  "https://example.com/a.mp4" \
  "https://example.com/b.mp4"

# 2) 传入两段本地视频，自动上传 + 拼接 + 下载到本地
python concat_video.py path/a.mp4 path/b.mp4 --output output/concat.mp4

# 3) 指定转场（中文名 / 英文别名 / ID 均可）
python concat_video.py a.mp4 b.mp4 --transition 梦幻放大
python concat_video.py a.mp4 b.mp4 --transition dream-zoom
python concat_video.py a.mp4 b.mp4 --transition 1182369
python concat_video.py a.mp4 b.mp4 --transition sunset,glitch

# 4) 强制硬切
python concat_video.py a.mp4 b.mp4 --no-transition

# 5) 查看全部可用转场
python concat_video.py --list-transitions

# 6) 透传额外参数（会合并进请求体）
python concat_video.py a.mp4 b.mp4 --param Project=my_project
```

### 4.4 退出码

- `0`：成功
- `1`：失败（参数错误、上传失败、接口报错、任务失败或超时）

---

## 5. 返回结果

### 5.1 命令行输出

```text
https://....vod.cn-north-1.volcvideo.com/xxxx.mp4?preview=1&auth_key=...
```

- stdout 仅打印**成片 URL**（便于脚本 `$(...)` 捕获）。
- 使用 `--output` 时，成片会下载到指定路径，并额外在 stderr 提示 `已下载到 ...`。

### 5.2 库调用返回

`concat_videos_to_url(...)` 直接返回成片 URL（string）。
`concat_videos(...)` 返回完整任务结果字典（见 5.3 的“完成”结构）。

```python
from concat_video import concat_videos_to_url, concat_videos, download_video

url = concat_videos_to_url([url1, url2], transitions=["梦幻放大"])
result = concat_videos([url1, url2])
print(result["result"]["video_url"], result["result"]["duration"])
download_video(url, "out.mp4")
```

### 5.3 接口返回格式

**创建任务** `POST /api/v1/tools/concat-video`：

```json
{
  "success": true,
  "task_id": "amk-tool-concat-video-1428900661762",
  "request_id": "20260923141555E9AD034C46F4530AF77E"
}
```

**查询任务** `GET /api/v1/tasks/{task_id}`：

进行中：

```json
{
  "success": true,
  "task_id": "amk-tool-concat-video-1428900661762",
  "task_type": "concat-video",
  "status": "running",
  "created_at": 1790144156,
  "request_id": "...",
  "queue_id": "..."
}
```

完成：

```json
{
  "success": true,
  "task_id": "amk-tool-concat-video-1428900661762",
  "task_type": "concat-video",
  "status": "completed",
  "result": {
    "duration": 36.166668,
    "resolution": "720p",
    "video_url": "https://....vod.cn-north-1.volcvideo.com/xxxx.mp4?preview=1&auth_key=..."
  },
  "expires_at": 1790230570,
  "created_at": 1790144156,
  "finished_at": 1790144170,
  "request_id": "...",
  "queue_id": "..."
}
```

失败（创建阶段参数错误）：

```json
{
  "success": false,
  "request_id": "...",
  "error": {
    "code": "InvalidParameter",
    "type": "BadRequest",
    "message": "validating root: ..."
  }
}
```

失败（任务执行阶段）：

```json
{
  "code": "InvalidParameter",
  "type": "BadRequest",
  "message": "remote node Edit error ..."
}
```

关键字段说明：

| 字段 | 说明 |
| --- | --- |
| `task_id` | 异步任务唯一标识，用于轮询 |
| `status` | `running` / `completed` / `failed` 等 |
| `result.duration` | 成片时长（秒） |
| `result.resolution` | 成片分辨率档位，如 `720p` |
| `result.video_url` | **成片地址**（未配置输出存储时为临时 HTTPS 链接，有效期 24 小时） |
| `expires_at` | 成片临时链接过期时间戳 |

> 成片临时链接**24 小时后失效**；需要长期保存请用 `--output` 下载到本地，
> 或配置 `media_output_destination` 输出到你的 TOS/VOD。

---

## 6. 接口调用流程

1. 创建任务

   ```bash
   curl -X POST 'https://mediakit.cn-beijing.volces.com/api/v1/tools/concat-video' \
     -H 'Authorization: Bearer <api_key>' \
     -H 'Content-Type: application/json' \
     -d '{
       "video_urls": ["https://.../a.mp4", "https://.../b.mp4"],
       "Project": "default",
       "transitions": ["1182369"]
     }'
   ```

2. 查询任务

   ```bash
   curl 'https://mediakit.cn-beijing.volces.com/api/v1/tasks/<task_id>' \
     -H 'Authorization: Bearer <api_key>'
   ```

3. `status == "completed"` 时读取 `result.video_url`。

---

## 7. 请求参数（concat-video）

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `video_urls` | array<string> | 是 | 待拼接素材，1–100 个；支持公网 URL、本地路径、`vod://`、`tos://`；单个建议 ≤ 10GB；最高 4K；多分辨率时以第一个为基准 |
| `transitions` | array<string> | 否 | 转场效果 ID 列表；**默认硬切**；数量不足时自动循环 |
| `Project` | string | 否 | 项目名 |
| `callback_url` | string | 否 | 任务结果回调地址 |
| `callback_args` | string | 否 | 自定义回调参数（≤512 字节） |
| `client_token` | string | 否 | 幂等令牌（≤64 个可打印 ASCII） |
| `queue_id` | string | 否 | 指定任务队列 |
| `media_output_destination` | string | 否 | 产物存储位置：`vod://<空间名>` 或 `tos://<桶名>` |

---

## 8. 转场（transitions）

`transitions` 是**字符串 ID 数组**。拼接 N 段需要 N-1 个转场；不足时自动循环。
工具支持用中文名 / 英文别名 / 原始 ID 指定：

| 名称 | 英文别名 | ID |
| --- | --- | --- |
| 交替出场 | alternating | 1182359 |
| 旋转放大 | rotate-zoom | 1182360 |
| 泛开 | spread | 1182358 |
| 六角形 | hexagon | 1182365 |
| 故障转换 | glitch | 1182367 |
| 飞眼 | fly-eye | 1182368 |
| 梦幻放大 | dream-zoom | 1182369 |
| 开门展现 | door-open | 1182370 |
| 立方转换 | cube | 1182373 |
| 透镜变换 | lens | 1182374 |
| 晚霞转场 | sunset | 1182375 |
| 圆形交替 | circle | 1182378 |

默认转场在 `config.json` 的 `transitions` 配置，命令行 `--transition` 优先。

---

## 9. 作为库调用

```python
from concat_video import (
    load_config, MediaKitClient, concat_videos, concat_videos_to_url,
    upload_file, download_video, resolve_transitions,
)

config = load_config()                       # 读取 edit_tool/config.json
client = MediaKitClient(config)

# 方式一：一步到位
url = concat_videos_to_url([url1, url2], transitions=["梦幻放大"])

# 方式二：手动控制生命周期
task_id = client.create_concat_task([url1, url2], transitions=["1182369"])
result = client.wait_for_task(task_id)
print(result["result"]["video_url"])

# 本地文件上传
public_url = upload_file("local.mp4", config["uploader"])
download_video(url, "out.mp4")
```

---

## 10. 常见问题

**Q：为什么拼接结果没有转场？**
A：`transitions` 是可选参数，**不传时接口默认硬切**。用 `--transition` 指定，或在
`config.json` 里配置 `transitions`。

**Q：本地文件能直接拼接吗？**
A：接口只接受公网 URL。工具会用 `uploader` 自动上传本地文件再拼接；也可加 `--no-upload`
强制只接受 URL。生产环境建议用 TOS/VOD。

**Q：为什么 catbox / tmpfiles 上传后任务失败？**
A：它们的直链不符合火山引擎的校验（catbox HEAD 长度为 0、tmpfiles 直链 302 跳转）。
请改用返回直接可下载直链的服务，默认配置使用 uguu。

**Q：成片链接打不开？**
A：临时链接有效期 24 小时，过期需重新生成，或用 `--output` 及时下载。

**Q：如何换成其他地区/域名？**
A：修改 `config.json` 的 `base_url`。

**Q：会泄露 API Key 吗？**
A：`config.json` 已在 `.gitignore` 中，不会提交；仓库只提交 `config.example.json` 模板。
