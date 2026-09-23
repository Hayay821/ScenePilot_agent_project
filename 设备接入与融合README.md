# Insta360 设备接入与项目融合说明

本文说明 BoldMaker 如何接入 Insta360 X5、Link 2，以及前端、设备桥、Device SDK 与 Cinematographer Session 之间的调用关系。

## 1. 当前架构

```text
浏览器
  │
  ├─ http://127.0.0.1:8765/app/create.html
  │       │
  │       ├─ 工作区、素材、Agent 对话
  │       └─ X5 / Link 2 设备控制界面
  │
  ├─ 8765：agents_Module_good
  │       ├─ 托管正式前端
  │       ├─ 提供 Agent API
  │       └─ 管理 Cinematographer Session
  │
  └─ 8766：device_bridge
          ├─ X5 CameraSDK
          ├─ X5 MediaSDK 实时拼接
          └─ Link 2 UVCCameraSDK
```

正式前端位于：

```text
agents_Module_good/front/
```

根目录旧的 `front/` 不再是设备融合的主入口。

## 2. 快速打开前端

### 2.1 不连接真实相机

安装依赖：

```powershell
cd agents_Module_good
python -m pip install -r requirements.txt
```

启动本地 Agent 服务：

```powershell
python fast.py serve --mode mock
```

浏览器打开：

```text
http://127.0.0.1:8765/app/create.html
```

这种方式可以查看完整前端、工作区、素材和 Agent 页面，但真实设备按钮需要 8766 设备服务。

### 2.2 运行完整设备 Demo

前提：

- Windows x64；
- Visual Studio 2022 Build Tools；
- CMake；
- FFmpeg；
- Insta360 CameraSDK；
- Insta360 MediaSDK；
- Insta360 Link 2 UVCCameraSDK。

官方 SDK 不在 GitHub 仓库中，需要开发者自行从影石取得。

确认并修改 `构建X5服务.ps1` 和 `启动X5真实服务.ps1` 中的 SDK 本机路径，然后执行：

```powershell
powershell -ExecutionPolicy Bypass -File ".\构建X5服务.ps1"
powershell -ExecutionPolicy Bypass -File ".\启动前端.ps1"
```

`启动前端.ps1` 会启动：

- 8765：`agents_Module_good`；
- 8766：X5/Link 2 真实设备桥；
- 浏览器页面：`/app/create.html`。

## 3. 前端如何调用设备

设备请求封装在：

```text
agents_Module_good/front/device-api.js
```

默认设备服务地址：

```text
http://127.0.0.1:8766/api/v1
```

主要接口：

| 功能 | 方法 | 地址 |
|---|---|---|
| 服务状态 | GET | `/health` |
| 设备列表 | GET | `/devices` |
| 连接设备 | POST | `/devices/{device_id}/connect` |
| 断开设备 | POST | `/devices/{device_id}/disconnect` |
| 执行动作 | POST | `/device-actions/execute` |
| X5 实时帧 | GET | `/streams/x5-main.jpg` |
| 拍摄素材列表 | GET | `/assets` |
| 保存 Link 2 图片 | POST | `/assets/link2-snapshot` |
| 保存 Link 2 视频 | POST | `/assets/link2-video` |

设备标识：

```text
x5-main
link2-main
```

动作请求示例：

```json
{
  "device_id": "x5-main",
  "action": "capture_photo",
  "parameters": {}
}
```

常用动作：

- `capture_photo`
- `start_recording`
- `stop_recording`
- `start_preview`
- `stop_preview`
- `set_tracking`
- `set_zoom`
- `set_privacy`
- `disconnect`

## 4. 统一 VideoFrame

X5 和 Link 2 的原始取帧方式不同：

- X5：CameraSDK 获取预览流，MediaSDK 实时拼接，然后输出 JPEG；
- Link 2：浏览器通过 UVC 获得 `MediaStream`，再使用 Canvas 截取 JPEG。

两者最终都由下面的文件转换：

```text
agents_Module_good/front/video-frame.js
```

统一格式：

```json
{
  "stream_id": "x5-main",
  "device_id": "x5-local",
  "source_type": "insta360_x5_mediasdk",
  "timestamp_ms": 1727000000000,
  "sequence": 1,
  "mime_type": "image/jpeg",
  "frame_data": "data:image/jpeg;base64,..."
}
```

Link 2 使用相同格式，只替换：

```json
{
  "stream_id": "link2-main",
  "device_id": "link2-local",
  "source_type": "insta360_link2_uvc"
}
```

## 5. 接入 Cinematographer Session

前端 Session 客户端：

```text
agents_Module_good/front/cinematographer-session.js
```

后端协议：

```text
agents_Module_good/api/schemas.py
```

后端接口：

```text
agents_Module_good/fast.py
```

调用顺序：

### 5.1 创建 Session

```http
POST /api/v1/agents/cinematographer/session/start
```

请求：

```json
{
  "user_text": "拍摄自然人像，保留人物和环境关系",
  "skills_filter": {
    "stage": "cinematographer",
    "limit": 3
  }
}
```

### 5.2 提交设备帧

```http
POST /api/v1/agents/cinematographer/session/{session_id}/frame
```

请求体直接使用统一 `VideoFrame`。

X5 和 Link 2 可以向同一个 `session_id` 提交帧。后端使用 `stream_id` 区分视频流，并为每路流保存独立的短期帧记忆。

### 5.3 停止 Session

```http
POST /api/v1/agents/cinematographer/session/{session_id}/stop
```

无需修改：

- 模型调用逻辑；
- 用户目标；
- Skill 选择；
- Session 生命周期；
- 用户对话逻辑。

设备层只负责把不同来源转换为统一 `VideoFrame`。

## 6. 前端中的使用方法

1. 打开创作页面；
2. 连接 X5 或 Link 2；
3. 点击“实时预览”；
4. 右侧选择“摄影师”；
5. 新建对话并输入拍摄目标；
6. 前端创建 Cinematographer Session；
7. 当前预览设备每 2.5 秒提交一帧；
8. 切换 X5/Link 2 时继续使用同一个 Session；
9. 返回对话列表时停止实时 Session。

## 7. 主要代码位置

| 模块 | 路径 | 作用 |
|---|---|---|
| 正式前端 | `agents_Module_good/front/create.html` | 工作区、Agent 和设备界面 |
| 设备 API | `agents_Module_good/front/device-api.js` | 调用 8766 设备服务 |
| 设备 UI | `agents_Module_good/front/device-console.js` | 连接、预览、拍照、录像 |
| 设备样式 | `agents_Module_good/front/device-console.css` | 设备面板样式 |
| 帧转换 | `agents_Module_good/front/video-frame.js` | X5/Link 2 转 VideoFrame |
| Session 客户端 | `agents_Module_good/front/cinematographer-session.js` | 创建、提交和停止 Session |
| 对话桥接 | `agents_Module_good/front/cinematographer-ui.js` | 摄影师对话与实时帧连接 |
| Session API | `agents_Module_good/fast.py` | Agent HTTP 接口 |
| 帧协议 | `agents_Module_good/api/schemas.py` | VideoFrame 请求字段 |
| 设备桥服务 | `device_bridge/x5_service/main.cpp` | 8766 本地 HTTP 服务 |
| X5 适配器 | `open-vide-vision-device-sdk/src/x5_camera_adapter.cpp` | CameraSDK + MediaSDK |
| Link 2 适配器 | `open-vide-vision-device-sdk/src/link2_camera_adapter.cpp` | UVCCameraSDK |
| SDK 构建 | `open-vide-vision-device-sdk/CMakeLists.txt` | 官方库链接和设备服务构建 |

## 8. 本地素材

设备拍摄素材保存在：

```text
agents_Module_good/data/camera_captures/
```

该目录被 `.gitignore` 排除，拍摄照片和视频不会上传 GitHub。

X5 原始文件可能是：

- `.insp`
- `.insv`
- `.jpg`
- `.mp4`

离线拼接和转码继续由 MediaSDK 或项目后期处理模块负责。

## 9. 不要提交官方 SDK

不要上传：

- CameraSDK.dll、MediaSDK.dll、UVCCamera.dll；
- 官方 `include/`、`lib/`、`bin/`；
- MediaSDK models；
- CameraSDK jsons；
- `device_bridge/runtime/`；
- `device_bridge/build-x5/`；
- 实际拍摄素材；
- API Key 和 `.env`。

仓库只提交：

- 项目自己的适配器；
- 设备桥源码；
- CMake 配置；
- 前端调用代码；
- 启动脚本；
- 接口文档。

## 10. Mock 与真实模型

设备桥始终调用真实 SDK，不使用 Mock。

`agents_Module_good` 默认可用 Mock 模式验证本地流程：

```powershell
python fast.py serve --mode mock
```

使用百炼真实模型：

```powershell
$env:DASHSCOPE_API_KEY = "自己的Key"
python fast.py serve --mode bailian
```

真实模型模式会把用户内容和提交的相机帧发送到百炼云端。API Key 只能保存在本机环境变量或未提交的 `.env` 中。

## 11. Git 协作建议

设备接入在独立分支开发：

```text
feature/insta360-device-integration
```

队友获取：

```powershell
git fetch origin
git switch feature/insta360-device-integration
git pull
```

验证完成后通过 Pull Request 合并到 `main`，避免直接覆盖队友正在修改的正式前端。