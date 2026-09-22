# Public API and backend mapping

## Stable application-facing interfaces

- `IDeviceAdapter`: lifecycle, capability discovery and typed device actions.
- `DeviceExecutor`: second-line approval/range checks, routing and audit output.
- `IMediaProcessor`: submit/query/cancel contract for panorama processing jobs.
- `DeviceAction`: the C++ form of `schemas/device_action.schema.json`.

## X5 CameraSDK 2.2.0 adapter

| Unified action | Official call |
|---|---|
| connect | `DeviceDiscovery::GetAvailableDevices`, `Camera::Open` |
| capture_photo | `Camera::TakePhoto` |
| start_recording | `Camera::StartRecording` |
| stop_recording | `Camera::StopRecording` |
| start_preview | `Camera::StartLiveStreaming` |
| stop_preview | `Camera::StopLiveStreaming` |
| download_media | `Camera::DownloadCameraFile` |
| shutdown | `Camera::ShutdownCamera` |

## Link 2 UVCCamera adapter

| Unified action | Official call |
|---|---|
| connect | `GetUVCCameraList` and controller construction |
| set_tracking | `UVCCameraExtendController::SetVideoMode` |
| set_composition | `SetCompositionStyle` |
| set_track_speed | `SetTrackSpeed` |
| set_ptz | extended `SetPanTiltAbsolute` |
| set_zoom | standard `SetZoomAbsolute` |
| set_privacy | `SetPrivacyMode` |

UVC pixels are captured by the host video-input layer (OpenCV, Media Foundation,
FFmpeg or WebRTC), while the vendor UVCCamera SDK controls PTZ, tracking and
camera-specific features.

## MediaSDK 3.1.7 processor

- `.insp` and Insta360 `.jpg` use `ImageStitcher::Stitch` synchronously.
- `.insv`, `.mp4` and `.lrv` use `VideoStitcher::StartStitch` asynchronously.
- `Get(job_id)` exposes progress and terminal state.
- `Cancel(job_id)` maps to `VideoStitcher::CancelStitch`.

## Recommended backend endpoints

The local backend can expose the C++ interfaces over HTTP or IPC:

- `GET /devices`
- `POST /device-actions/validate`
- `POST /device-actions/execute`
- `GET /device-actions/{request_id}`
- `POST /media-jobs`
- `GET /media-jobs/{job_id}`
- `POST /media-jobs/{job_id}/cancel`

Every execute request must already contain a `rule_id`, `evidence_id` and
PlanValidator approval. The backend persists the returned `AuditRecord` for the
director timeline.
