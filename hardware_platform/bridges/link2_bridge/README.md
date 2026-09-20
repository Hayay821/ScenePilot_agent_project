# Link 2 Bridge - UVC Camera SDK 集成

Link 2 云台相机的 C++ 设备桥，基于官方 Link-SDK。

## 功能

- USB UVC 设备发现和枚举
- Pan/Tilt 绝对位置控制
- 自动追踪和目标选择
- 视频模式和构图设置
- 手势控制
- HTTP API 服务器
- WebSocket 事件流

## 前置条件

### 硬件
- Link 2 云台相机（USB 连接）

### 软件
- CMake 3.20+
- C++17 编译器
  - Windows: Visual Studio 2019+
  - Linux: GCC 9+ / Clang 10+
- Link-SDK (官方)

### 依赖库
- httplib (HTTP 服务器)
- websocketpp (WebSocket 服务器)
- nlohmann/json (JSON 解析)

## 编译

### Windows

```bash
# 设置 Link-SDK 路径
set LINK_SDK_PATH=C:\path\to\Link-SDK

# 创建构建目录
mkdir build
cd build

# 生成项目文件
cmake .. -G "Visual Studio 16 2019" -A x64

# 编译
cmake --build . --config Release
```

### Linux

```bash
# 设置 Link-SDK 路径
export LINK_SDK_PATH=/path/to/Link-SDK

# 创建构建目录
mkdir build
cd build

# 生成 Makefile
cmake .. -DCMAKE_BUILD_TYPE=Release

# 编译
make -j$(nproc)
```

## 运行

```bash
# 查看帮助
./link2_bridge --help

# 启动服务（默认端口 8002）
./link2_bridge --port 8002

# 指定日志级别
./link2_bridge --port 8002 --log-level debug
```

## API 端点

### 能力查询

```
GET /v1/capabilities
```

响应:
```json
{
  "device_id": "link2-serial-123",
  "device_type": "link2",
  "firmware_version": "1.2.3",
  "serial_number": "LINK2123456",
  "capabilities": {
    "video_stream": true,
    "pan_tilt_absolute": true,
    "pan_range": [-145.0, 145.0],
    "tilt_range": [-45.0, 90.0],
    "tracking": true,
    "composition": ["head", "half_body", "full_body"],
    "gesture": true,
    "audio": true
  }
}
```

### 命令提交

```
POST /v1/commands
Content-Type: application/json

{
  "command_id": "cmd-001",
  "action": "set_pan_tilt_absolute",
  "args": {
    "pan_deg": 20.0,
    "tilt_deg": 5.0
  },
  "deadline_ms": 1000
}
```

响应:
```json
{
  "command_id": "cmd-001",
  "status": "success",
  "result": {
    "pan_actual": 20.1,
    "tilt_actual": 5.0
  },
  "error": null,
  "execution_time_ms": 156.3
}
```

### 事件流

```
WebSocket /v1/events
```

事件示例:
```json
{
  "event_id": "evt-001",
  "device_id": "link2-serial-123",
  "event_type": "ptz_position_changed",
  "timestamp": "2024-03-20T10:30:00Z",
  "data": {
    "pan_deg": 20.1,
    "tilt_deg": 5.0
  },
  "severity": "info",
  "message": "PTZ position changed"
}
```

## 支持的命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `set_pan_tilt_absolute` | `pan_deg`, `tilt_deg` | 绝对位置控制 |
| `ptz_stop` | - | 停止云台运动 |
| `ptz_home` | - | 返回 Home 位置 |
| `start_tracking` | `target_id` (可选) | 开始自动追踪 |
| `stop_tracking` | - | 停止追踪 |
| `set_track_target` | `target_id` | 选择追踪目标 |
| `set_track_speed` | `speed` | 设置追踪速度 |
| `set_composition_style` | `style` | 设置构图风格 |
| `set_video_mode` | `mode` | 设置视频模式 |
| `enable_gesture` | - | 启用手势控制 |
| `disable_gesture` | - | 禁用手势控制 |

## 安全约束

### 范围检查
- Pan: [-145°, 145°]
- Tilt: [-45°, 90°]
- 越界命令返回 `invalid_args`

### 速率限制
- 最大命令速率: 10 cmd/s
- 超过限制返回 429

### 超时保护
- 默认命令超时: 1000ms
- 超时自动发送 PTZ Stop

### 退出清理
- 程序退出前自动发送 PTZ Stop
- 释放 UVC 控制器资源

## 开发

### 目录结构

```
link2_bridge/
├── src/
│   ├── main.cpp              # 主程序入口
│   ├── device_manager.cpp    # Link SDK 设备管理
│   ├── http_server.cpp       # HTTP 服务器
│   ├── websocket_server.cpp  # WebSocket 服务器
│   └── command_executor.cpp  # 命令执行器
├── include/
│   ├── device_manager.h
│   ├── http_server.h
│   ├── websocket_server.h
│   └── command_executor.h
├── CMakeLists.txt
└── README.md
```

### 添加新命令

1. 在 `command_executor.h` 添加命令处理方法
2. 在 `command_executor.cpp` 实现命令逻辑
3. 在 `http_server.cpp` 注册命令路由
4. 更新 API 文档

## 故障排除

### 设备未找到

```bash
# 检查 USB 连接
lsusb | grep Insta360

# 检查设备权限（Linux）
sudo chmod 666 /dev/video*
```

### 编译错误

```bash
# 确认 Link-SDK 路径
echo $LINK_SDK_PATH

# 清理重新编译
rm -rf build
mkdir build && cd build
cmake .. && make
```

### 运行时错误

```bash
# 检查端口占用
netstat -an | grep 8002

# 查看详细日志
./link2_bridge --port 8002 --log-level debug
```

## 参考

- [Link-SDK GitHub](https://github.com/Insta360Develop/Link-SDK)
- [Link UVC 开发者文档](https://insta360develop.github.io/Insta360-Developer_Docs/ch/link/uvc/guide/)
- [02-明天硬件与云平台接入设计.md](../../doc/02-明天硬件与云平台接入设计.md)
