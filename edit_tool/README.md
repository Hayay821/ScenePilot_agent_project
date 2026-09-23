# edit_tool

调用火山引擎 MediaKit 的 **视频拼接（concat-video）** 工具：传入两个及以上视频（或图片），
接口会拼接并可添加转场，返回拼接好的成片地址。

> 完整文档（配置、参数、返回格式、接口流程等）见 [DOCUMENTATION.md](./DOCUMENTATION.md)。

支持两种输入：

- 公网 `http(s)` URL；
- 本地视频/图片文件路径（工具会先上传到文件托管服务，再拿公网 URL 去拼接）。

## 配置

1. 复制模板并填入自己的 API Key：

   ```bash
   cp config.example.json config.json
   ```

2. `config.json` 字段说明：

   | 字段 | 说明 |
   | --- | --- |
   | `api_key` | 火山引擎 MediaKit API Key（必填） |
   | `base_url` | 接口域名，默认 `https://mediakit.cn-beijing.volces.com` |
   | `project` | 项目名，默认 `default` |
   | `timeout_seconds` | 单次 HTTP 请求超时 |
   | `poll_interval_seconds` | 任务轮询间隔 |
   | `poll_timeout_seconds` | 任务轮询总超时 |
   | `uploader` | 本地文件上传配置（见下） |

   `uploader` 默认使用 uguu（返回直链，火山引擎可正常拉取）：

   ```json
   {
     "enabled": true,
     "url": "https://uguu.se/upload.php",
     "file_field": "files[]",
     "extra_fields": {},
     "response_path": "files.0.url"
   }
   ```

   可替换为其他服务：
   - `response_path`：从 JSON 响应里按点路径取 URL，如 `files.0.url`；
   - `url_replace`：对取到的 URL 做前缀替换，如 `["旧前缀", "新前缀"]`（用于需要改写直链的服务）。

   > 注意：部分托管服务的直链会被火山引擎判定为不可用——例如 catbox 的 HEAD 返回长度为 0、tmpfiles 的直链会 302 跳转，都会导致任务失败。请选择返回直接、可直接下载 URL 的服务。

> `config.json` 含密钥，已加入 `.gitignore`，不会上传到 GitHub；仓库只提交 `config.example.json` 模板。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 传入两个公网素材 URL，打印成片地址
python concat_video.py \
  "https://lf3-static.bytednsdoc.com/obj/eden-cn/ljhwz_kvc/ljhwZthlaukjlkulzlp/ai_mediakit/ToolDetails/ConcatVideo_B4_1.mp4" \
  "https://lf3-static.bytednsdoc.com/obj/eden-cn/ljhwz_kvc/ljhwZthlaukjlkulzlp/ai_mediakit/ToolDetails/ConcatVideo_B4_2.mp4"

# 传入两段本地视频，自动上传并拼接，再下载到本地
python concat_video.py path/a.mp4 path/b.mp4 --output output/concat.mp4

# 透传额外参数
python concat_video.py URL1 URL2 --param Transition=dissolve

# 禁止自动上传（只接受 URL）
python concat_video.py URL1 URL2 --no-upload

# 使用其他配置文件
python concat_video.py URL1 URL2 --config /path/to/config.json

# 指定转场（可多次或用逗号分隔，支持中文名/英文别名/ID）
python concat_video.py a.mp4 b.mp4 --transition 梦幻放大 --output output/out.mp4
python concat_video.py a.mp4 b.mp4 --transition sunset,glitch

# 强制硬切（不添加转场）
python concat_video.py a.mp4 b.mp4 --no-transition

# 查看所有可用转场
python concat_video.py --list-transitions
```

## 转场（transitions）

接口的 `transitions` 是**字符串 ID 数组**；**不传时默认硬切（没有转场）**。
拼接 N 段视频需要 N-1 个转场；转场数量不足时，接口会自动循环使用。

工具支持用中文名 / 英文别名 / 原始 ID 指定，映射如下：

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

默认转场在 `config.json` 的 `transitions` 配置（示例为 `["交替出场"]`）；命令行 `--transition` 会覆盖它。

## 作为库调用

```python
from concat_video import concat_videos_to_url, download_video, upload_file, load_config

config = load_config()
url = concat_videos_to_url([url1, url2])
download_video(url, "out.mp4")
```

## 接口流程

1. `POST /api/v1/tools/concat-video`
   请求体：`{"video_urls": [...], "Project": "default"}`
   返回：`{"success": true, "task_id": "..."}`
2. `GET /api/v1/tasks/{task_id}` 轮询任务状态
   - `running`：继续等待
   - `completed`：`result.video_url` 即拼接好、带转场的成片地址
   - `failed`：抛出错误

> 云端只能访问公网 URL，本地文件会先通过 `uploader` 上传。
> 图片同样以 URL 形式传入 `video_urls`。
> 返回的成片地址带签名，`expires_at` 之后会失效，需要长期保存请用 `--output` 下载到本地。
