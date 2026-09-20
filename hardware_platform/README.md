# Hardware Platform - 硬件设备接入平台

ScenePilot 硬件设备层，负责 X4 Air 全景相机和 Link 2 云台相机的真实 SDK 集成。

## 架构概览

```
Python AI Service (algorithm_validation/)
  │
  ├─> x4air_bridge (C++ localhost:8001)
  │     ├─ Desktop Camera SDK: USB 控制、预览、录制
  │     ├─ Desktop Media SDK: .insv 拼接、equirectangular 导出
  │     └─ OSC fallback: Wi-Fi HTTP 备选
  │
  └─> link2_bridge (C++ localhost:8002)
        ├─ UVC video capture: 视频流读取
        ├─ UVCCameraController: PTZ/曝光/对焦/画质
        └─ UVCCameraExtendController: 追踪/构图/手势
```

## 目录结构

```
hardware_platform/
├── bridges/                    # C++ 设备桥服务
│   ├── link2_bridge/          # Link 2 UVC SDK 集成
│   │   ├── src/
│   │   │   ├── main.cpp
│   │   │   ├── device_manager.cpp
│   │   │   ├── http_server.cpp
│   │   │   └── websocket_server.cpp
│   │   ├── include/
│   │   ├── CMakeLists.txt
│   │   └── README.md
│   │
│   ├── x4air_bridge/          # X4 Air Camera SDK 集成
│   │   ├── src/
│   │   │   ├── main.cpp
│   │   │   ├── camera_controller.cpp
│   │   │   ├── http_server.cpp
│   │   │   └── websocket_server.cpp
│   │   ├── include/
│   │   ├── CMakeLists.txt
│   │   └── README.md
│   │
│   └── media_worker/           # X4 Air Media SDK 工作器
│       ├── src/
│       │   ├── main.cpp
│       │   ├── stitcher.cpp
│       │   └── http_server.cpp
│       ├── include/
│       ├── CMakeLists.txt
│       └── README.md
│
├── adapters/                   # Python 设备适配器
│   ├── __init__.py
│   ├── base.py                # 基础适配器接口
│   ├── link2_adapter.py       # Link 2 适配器
│   ├── x4air_adapter.py       # X4 Air 适配器
│   └── mock_adapter.py        # Mock 适配器（测试用）
│
├── protocols/                  # 统一设备协议定义
│   ├── __init__.py
│   ├── capabilities.py        # 能力查询协议
│   ├── commands.py            # 命令提交协议
│   └── events.py              # 事件流协议
│
├── edge/                       # 边缘代理（现场电脑）
│   ├── __init__.py
│   ├── agent.py               # 边缘代理主程序
│   ├── local_control.py       # 本地 PTZ 闭环控制
│   └── cloud_sync.py          # 云端同步
│
├── tests/                      # 测试
│   ├── test_link2_adapter.py
│   ├── test_x4air_adapter.py
│   └── test_protocols.py
│
├── .env.example
├── requirements.txt
└── README.md
```

## 核心概念

### 1. 设备桥 (Device Bridge)

C++ 独立进程，封装官方 SDK，通过 HTTP/WebSocket 提供统一接口：

- **Link 2 Bridge**: 基于 Link-SDK，控制云台 PTZ、追踪、构图
- **X4 Air Bridge**: 基于 Desktop Camera SDK，控制录制、预览、文件管理
- **Media Worker**: 基于 Desktop Media SDK，离线拼接 .insv → .mp4

### 2. 统一协议

所有设备桥遵循统一协议：

- **能力查询**: `GET /v1/capabilities` 返回设备支持的功能列表
- **命令提交**: `POST /v1/commands` 提交控制命令，返回执行结果
- **事件流**: `WebSocket /v1/events` 实时推送设备状态变化

### 3. Python 适配器

包装设备桥 HTTP 客户端，转换为 `algorithm_validation` 使用的 `CameraAction` 接口：

- 能力缓存
- 超时重试
- 熔断降级
- Mock fallback

### 4. 边缘/云端分工

- **边缘代理**: 本地检测跟踪、高频 PTZ 闭环、STC 压缩
- **云端服务**: 语义分析、事件管理、Web UI、存储
- **断网 resilience**: 本地 outbox 队列，恢复后补传

## 快速开始

### 前置条件

1. **硬件**:
   - X4 Air 全景相机 (USB 连接)
   - Link 2 云台相机 (USB 连接)

2. **软件**:
   - Windows 10+ / Ubuntu 22.04
   - Python 3.11
   - CMake 3.20+
   - Visual Studio 2019+ (Windows) / GCC 9+ (Linux)
   - 独立 GPU (Media SDK 需要)

3. **SDK**:
   - [Link-SDK](https://github.com/Insta360Develop/Link-SDK)
   - Desktop Camera SDK (官方下载)
   - Desktop Media SDK (官方下载)

### 第一步: 硬件能力探测

在开始开发前，必须先验证硬件能力：

```bash
cd hardware_platform

# Link 2 能力探测
python scripts/probe_link2.py

# X4 Air 能力探测
python scripts/probe_x4air.py
```

保存能力探测结果到 `data/capabilities/`，后续开发以实测能力为准。

### 第二步: 编译设备桥

#### Link 2 Bridge

```bash
cd bridges/link2_bridge
mkdir build && cd build
cmake ..
cmake --build . --config Release

# 运行
./link2_bridge --port 8002
```

#### X4 Air Bridge

```bash
cd bridges/x4air_bridge
mkdir build && cd build
cmake ..
cmake --build . --config Release

# 运行
./x4air_bridge --port 8001
```

### 第三步: 测试 Python 适配器

```bash
# 安装依赖
pip install -r requirements.txt

# 测试 Link 2 适配器
python -m pytest tests/test_link2_adapter.py -v

# 测试 X4 Air 适配器
python -m pytest tests/test_x4air_adapter.py -v
```

### 第四步: 运行边缘代理

```bash
# 配置环境变量
cp .env.example .env
# 编辑 .env 填入真实配置

# 启动边缘代理
python -m edge.agent \
  --link2-bridge http://localhost:8002 \
  --x4air-bridge http://localhost:8001 \
  --cloud-endpoint https://your-cloud-service.com \
  --local-mode  # 断网测试模式
```

## 开发任务

### Task A: Link 2 C++ Bridge (3-4 小时)

基于官方 Link-SDK 示例创建最小 C++ 服务：

- [x] 设备枚举和能力查询
- [x] Pan/Tilt 绝对位置控制
- [x] 视频模式、构图、追踪目标设置
- [x] HTTP API 服务器 (httplib)
- [x] WebSocket 事件流 (websocketpp)
- [x] 安全保护：范围检查、超时、Stop 命令

### Task B: X4 Air Camera Bridge (3-4 小时)

基于 Desktop Camera SDK 示例：

- [x] USB 设备发现和连接
- [x] 开始/停止录像
- [x] 预览流
- [x] 文件列表和下载
- [x] HTTP API 服务器
- [x] WebSocket 事件流
- [ ] OSC fallback 实现 (可选)

### Task C: X4 Air Media Worker (2 小时)

基于 Desktop Media SDK 示例：

- [x] `.insv` → `equirectangular.mp4` 离线拼接
- [x] 任务队列、进度、日志
- [x] GPU 检查
- [x] UTF-8 路径处理

### Task D: Python Adapter (1 小时)

- [x] `Link2DeviceAdapter` 和 `X4AirDeviceAdapter`
- [x] 统一 `CameraAction` 接口
- [x] 能力缓存、超时、熔断、Mock fallback

### Task E: Edge/Cloud 分工 (2 小时)

- [x] Edge Agent: 本地检测跟踪、PTZ 闭环、关键帧上传
- [x] Cloud Service: 语义分析、事件管理、Web UI
- [x] 断网 resilience: 本地 outbox 队列

## 安全约束

### 云台控制安全

- Pan/Tilt 范围检查: `[-145°, 145°]` / `[-45°, 90°]`
- 速率限制: 最大 10 cmd/s
- 超时保护: 所有命令 1s 超时自动停止
- 异常退出: 发送 PTZ Stop 并释放控制器

### 录制控制安全

- 不允许 LLM 调用固件升级、恢复出厂、格式化
- 删除素材需要二次确认
- 人脸/声音素材取得授权

### 网络安全

- 设备桥只监听 localhost 或受控局域网
- API Key、OSS 凭证放在环境变量
- 云端使用服务端签名或短期 STS

## 降级策略

### SDK 不可用

- **Link 2**: 降级到 OpenCV UVC 视频流 + 手动 PTZ
- **X4 Air**: 降级到 OSC HTTP 控制

### 网络不可用

- 边缘代理继续本地跟拍
- 事件写入 outbox 队列
- 恢复后补传

### GPU 不可用

- Media SDK 自动降级到 CPU 拼接 (较慢)
- 或使用官方 Studio 预先导出

## 文档参考

- [02-明天硬件与云平台接入设计.md](../doc/02-明天硬件与云平台接入设计.md)
- [Link-SDK 文档](https://insta360develop.github.io/Insta360-Developer_Docs/ch/link/uvc/guide/)
- [X 系列桌面端 SDK](https://insta360develop.github.io/Insta360-Developer_Docs/ch/x/desktop/camera/)

## License

内部开发使用，遵循影石 SDK 许可协议
