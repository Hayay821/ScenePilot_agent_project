# Open Vide Vision 设备 SDK

这是一个 C++17 设备集成层，用于在 Windows 系统上连接 Open Vide Vision 多 Agent 架构、Insta360 X5 和 Insta360 Link 2。

## 仓库包含的内容

- 与厂商实现解耦的 `IDeviceAdapter` 统一设备接口。
- 负责权限、能力和参数校验的 `DeviceExecutor` 设备执行边界。
- 采用异步任务形式设计的 `IMediaProcessor` 媒体处理接口。
- 用于校验 Agent 设备动作的 JSON Schema。
- 不依赖影石专有文件即可运行的模拟设备和模拟媒体处理器。
- CameraSDK 2.2.0、MediaSDK 3.1.7 和 Link 2 UVCCamera SDK 的可选真实适配器。
- Windows x64 配置、接口映射、技术架构和 GitHub 提交说明。

本仓库不包含影石官方 SDK 的 DLL、LIB、头文件、模型、JSON 能力文件或压缩包。开发者需要通过影石官方渠道单独取得这些依赖。

## 在系统中的位置

```text
导演/摄影指导/剪辑 Agent
            ↓
       结构化导演计划
            ↓
       PlanValidator
            ↓
      已批准的设备动作
            ↓
       DeviceExecutor
       ↙             ↘
X5 设备适配器      Link 2 设备适配器
       ↓
  CameraSDK / UVCCamera SDK
       ↓
      物理设备
```

X5 下载的 `.insp`、`.insv` 等素材会进入 `IMediaProcessor`，再由 MediaSDK 完成图片拼接、视频拼接、进度报告和任务取消。

## 为什么需要这一层

Agent 不能直接调用 CameraSDK、MediaSDK 或 UVCCamera SDK。所有动作必须先形成结构化请求，再经过 `PlanValidator` 和 `DeviceExecutor`。

这样可以保证：

- 检查用户或 Skill 是否具有设备控制权限。
- 检查目标设备是否支持对应能力。
- 限制云台角度、变焦范围和文件路径。
- 将每次设备动作关联到 `rule_id` 和 `evidence_id`。
- 保存动作结果，生成可审计的导演时间线。
- 避免上层业务依赖厂商SDK的数据结构。
- 将真实设备替换为模拟设备时，不修改 Agent 和业务代码。

## 支持的设备能力

### Insta360 X5

通过 CameraSDK 2.2.0 提供：

- 发现和连接相机。
- 拍摄照片。
- 开始、停止录像。
- 开始、停止实时预览。
- 下载相机素材。
- 关闭相机。

通过 MediaSDK 3.1.7 提供：

- `.insp` 和影石 `.jpg` 图片拼接。
- `.insv`、`.mp4`、`.lrv` 视频拼接。
- FlowState 防抖和方向锁定。
- 图片、视频输出分辨率设置。
- 视频任务进度查询与取消。

### Insta360 Link 2

通过 UVCCamera SDK 提供：

- 自动跟踪开关。
- 头像、半身、全身构图。
- 跟踪速度。
- 云台 PTZ 控制。
- 变焦。
- 隐私模式。

Link 2 的视频像素流应由 Windows UVC 视频输入层获取，例如 OpenCV、Media Foundation、FFmpeg 或 WebRTC。UVCCamera SDK 主要负责设备控制。

## 构建模拟版本

模拟版本不需要官方 SDK，适合 Agent、后端和前端团队并行开发。

```powershell
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```

运行示例：

```powershell
.\build\Debug\ovv_device_demo.exe
```

如果使用单配置生成器，程序可能位于：

```powershell
.\build\ovv_device_demo.exe
```

## 接入真实 SDK

真实设备版本必须使用 Windows x64 和 MSVC 工具链。配置示例：

```powershell
cmake -S . -B build -A x64 `
  -DOVV_ENABLE_X5_CAMERA=ON `
  -DINSTA360_CAMERA_SDK_ROOT="D:/SDK/CameraSDK-2.2.0" `
  -DOVV_ENABLE_LINK_UVC=ON `
  -DINSTA360_LINK_SDK_ROOT="D:/SDK/UVCCamera_win/x64" `
  -DOVV_ENABLE_MEDIA_SDK=ON `
  -DINSTA360_MEDIA_SDK_ROOT="D:/SDK/MediaSDK-3.1.7"

cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

运行时还需要把官方 DLL、X5 的 `jsons` 和 MediaSDK 的 `models` 等资源部署到程序旁边。详细步骤见 `docs/VENDOR_SETUP.md`。

## 核心公共接口

- `IDeviceAdapter`：统一设备生命周期、能力发现和动作执行。
- `DeviceExecutor`：执行审批、参数校验、设备路由和审计。
- `IMediaProcessor`：提交、查询和取消媒体处理任务。
- `DeviceAction`：经过 PlanValidator 校验后的设备动作。
- `AuditRecord`：一次物理设备动作的审计记录。

## 目录说明

```text
include/ovv/                 对外公开的 C++ 接口
src/                         模拟实现和三个官方 SDK 适配器
schemas/                     Agent 设备动作 JSON Schema
config/                      设备配置示例
docs/                        架构、接口、SDK安装和提交说明
examples/                    最小调用示例
tests/                       DeviceExecutor 基础测试
third_party/insta360/        第三方依赖说明，不存放官方文件
```

## 相关文档

- `docs/ARCHITECTURE.md`：与多 Agent 技术架构的连接方式。
- `docs/API.md`：统一动作和官方 API 的对应关系。
- `docs/VENDOR_SETUP.md`：Windows 官方 SDK 安装与构建方法。
- `docs/GITHUB_CHECKLIST.md`：提交 GitHub 前的检查项目。

## 第三方依赖声明

影石官方 SDK 及其附带文件不属于本仓库 MIT 许可证的授权范围。使用者必须自行取得官方 SDK，并遵守对应协议。
