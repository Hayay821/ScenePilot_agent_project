# X4 Air Bridge - Desktop Camera SDK 集成

X4 Air 全景相机的 C++ 设备桥，基于官方 Desktop Camera SDK。

## 功能

- USB 设备发现和连接
- 开始/停止录像
- 预览流
- 文件列表和下载（X4 及后续机型支持）
- HTTP API 服务器
- WebSocket 事件流
- OSC 协议 fallback（可选）

## 前置条件

### 硬件
- X4 Air 全景相机（USB 连接）

### 软件
- CMake 3.20+
- C++17 编译器
  - Windows: Visual Studio 2019+
  - Linux: GCC 9+ / Clang 10+
- Desktop Camera SDK (官方下载)

### 依赖库
- httplib (HTTP 服务器)
- websocketpp (WebSocket 服务器)
- nlohmann/json (JSON 解析)

## 编译

### Windows

```bash
# 设置 Camera SDK 路径
set CAMERA_SDK_PATH=C:\path\to\Desktop-Camera-SDK

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
# 设置 Camera SDK 路径
export CAMERA_SDK_PATH=/path/to/Desktop-Camera-SDK

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
./x4air_bridge --help

# 启动服务（默认端口 8001）
./x4air_bridge --port 8001

# 指定日志级别
./x4air_bridge --port 8001 --log-level debug
```

## API 端点

### 能力查询

```
GET /v1/capabilities
```

响应:
```json
{
  "device_id": "x4air-serial-456",
  "device_type": "x4_air",
  "firmware_version": "2.1.0",
  "serial_number": "X4AIR456789",
  "capabilities": {
    "remote_control": true,
    "file_download": true,
    "preview_stream": true,
    "resolutions": [[7680, 3840], [5760, 2880]],
    "frame_rates": [30, 25, 24],
    "formats": ["insv"]
  }
}
```

### 命令提交

```
POST /v1/commands
Content-Type: application/json

{
  "command_id": "cmd-001",
  "action": "start_recording",
  "args": {},
  "deadline_ms": 5000
}
```

响应:
```json
{
  "command_id": "cmd-001",
  "status": "success",
  "result": {
    "file_path": "/DCIM/Camera01/VID_20240320_100000_00_001.insv"
  },
  "error": null,
  "execution_time_ms": 823.5
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
  "device_id": "x4air-serial-456",
  "event_type": "recording_started",
  "timestamp": "2024-03-20T10:30:00Z",
  "data": {
    "file_path": "/DCIM/Camera01/VID_20240320_100000_00_001.insv"
  },
  "severity": "info",
  "message": "Recording started"
}
```

## 支持的命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `start_recording` | - | 开始录像 |
| `stop_recording` | - | 停止录像 |
| `take_photo` | - | 拍照 |
| `start_preview` | - | 开始预览流 |
| `stop_preview` | - | 停止预览流 |
| `list_files` | - | 列出文件（X4+） |
| `download_file` | `file_path`, `local_path` | 下载文件（X4+） |
| `delete_file` | `file_path` | 删除文件 |

## 注意事项

### 文件下载
- 官方文档注明文件下载适用于 X4 及后续机型
- X4 Air 需要现场验证是否支持
- 如不支持，需通过 Wi-Fi + OSC 协议下载

### USB 连接
- 确保使用 USB 数据线（非充电线）
- 相机需要开机状态
- Windows 可能需要安装驱动

### 录制限制
- 同一时间只能有一个录制会话
- 停止录制前检查录制状态
- 录制文件为 .insv 双鱼眼格式，需 Media SDK 拼接

## OSC 协议 fallback

如果 USB SDK 不稳定，可使用 OSC 协议：

```bash
# 编译时启用 OSC 支持
cmake .. -DENABLE_OSC=ON

# 运行时指定相机 Wi-Fi 地址
./x4air_bridge --port 8001 --osc-url http://192.168.42.1
```

## 故障排除

### 设备未找到

```bash
# Windows: 检查设备管理器
# Linux: 检查 USB 设备
lsusb | grep Insta360

# 确认相机已开机
```

### 编译错误

```bash
# 确认 Camera SDK 路径
echo $CAMERA_SDK_PATH

# 清理重新编译
rm -rf build
mkdir build && cd build
cmake .. && make
```

### 录制失败

```bash
# 检查存储卡
# 检查相机电量
# 查看详细日志
./x4air_bridge --log-level debug
```

## 参考

- [Desktop Camera SDK 文档](https://insta360develop.github.io/Insta360-Developer_Docs/ch/x/desktop/camera/)
- [02-明天硬件与云平台接入设计.md](../../doc/02-明天硬件与云平台接入设计.md)
