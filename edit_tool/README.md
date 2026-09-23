# edit_tool

调用火山引擎 MediaKit 的 **视频拼接（concat-video）** 工具：传入两个及以上视频（或图片）URL，
接口会拼接并自动添加转场，返回拼接好的成片地址。

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

> `config.json` 含密钥，已加入 `.gitignore`，不会上传到 GitHub；仓库只提交 `config.example.json` 模板。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
# 传入两个素材 URL，打印成片地址
python concat_video.py \
  "https://lf3-static.bytednsdoc.com/obj/eden-cn/ljhwz_kvc/ljhwZthlaukjlkulzlp/ai_mediakit/ToolDetails/ConcatVideo_B4_1.mp4" \
  "https://lf3-static.bytednsdoc.com/obj/eden-cn/ljhwz_kvc/ljhwZthlaukjlkulzlp/ai_mediakit/ToolDetails/ConcatVideo_B4_2.mp4"

# 同时下载到本地
python concat_video.py URL1 URL2 --output output/concat.mp4

# 透传额外参数
python concat_video.py URL1 URL2 --param Transition=dissolve

# 使用其他配置文件
python concat_video.py URL1 URL2 --config /path/to/config.json
```

## 作为库调用

```python
from concat_video import concat_videos_to_url, download_video

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

> 输入必须是可公网访问的 `http(s)` URL，云端无法访问本地文件路径。
> 图片同样以 URL 形式传入 `video_urls`。
> 返回的成片地址带签名，`expires_at` 之后会失效，需要长期保存请先下载到本地。
