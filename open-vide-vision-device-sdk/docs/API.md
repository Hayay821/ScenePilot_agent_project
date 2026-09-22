# 公共接口与官方 SDK 映射

## 对上层稳定的接口

- `IDeviceAdapter`：设备连接、断开、能力查询和动作执行。
- `DeviceExecutor`：审批检查、参数检查、动作路由和审计输出。
- `IMediaProcessor`：提交、查询、取消全景媒体处理任务。
- `DeviceAction`：`schemas/device_action.schema.json` 在 C++ 中的结构。

## X5 CameraSDK 2.2.0 适配器

| 统一动作 | 官方调用 |
|---|---|
| 连接设备 | `DeviceDiscovery::GetAvailableDevices`、`Camera::Open` |
| 拍照 | `Camera::TakePhoto` |
| 开始录像 | `Camera::StartRecording` |
| 停止录像 | `Camera::StopRecording` |
| 开始预览 | `Camera::StartLiveStreaming` |
| 停止预览 | `Camera::StopLiveStreaming` |
| 下载素材 | `Camera::DownloadCameraFile` |
| 关闭相机 | `Camera::ShutdownCamera` |

## Link 2 UVCCamera 适配器

| 统一动作 | 官方调用 |
|---|---|
| 连接设备 | `GetUVCCameraList`，然后创建控制器 |
| 自动跟踪 | `UVCCameraExtendController::SetVideoMode` |
| 构图样式 | `SetCompositionStyle` |
| 跟踪速度 | `SetTrackSpeed` |
| 云台角度 | 扩展控制器的 `SetPanTiltAbsolute` |
| 变焦 | 标准控制器的 `SetZoomAbsolute` |
| 隐私模式 | `SetPrivacyMode` |

Link 2 的视频画面由主机UVC输入层获取；厂商SDK负责PTZ、跟踪、构图等设备控制。

## MediaSDK 3.1.7 处理器

- `.insp` 和影石 `.jpg` 通过 `ImageStitcher::Stitch` 同步处理。
- `.insv`、`.mp4`、`.lrv` 通过 `VideoStitcher::StartStitch` 异步处理。
- `Get(job_id)` 查询进度和最终状态。
- `Cancel(job_id)` 对应 `VideoStitcher::CancelStitch`。

## 建议的本地后端接口

- `GET /devices`：查询设备和能力。
- `POST /device-actions/validate`：校验动作。
- `POST /device-actions/execute`：执行已批准动作。
- `GET /device-actions/{request_id}`：查询执行结果。
- `POST /media-jobs`：提交媒体处理任务。
- `GET /media-jobs/{job_id}`：查询任务进度。
- `POST /media-jobs/{job_id}/cancel`：取消任务。

每个执行请求都必须包含 `rule_id`、`evidence_id` 和 PlanValidator 审批结果。后端应持久化 `AuditRecord`，供导演时间线和问题追踪使用。
