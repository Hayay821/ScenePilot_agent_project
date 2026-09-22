# 技术架构接入说明

```text
导演 / 摄影指导 / 剪辑 Agent
                 |
          结构化 DeviceAction
                 v
            PlanValidator
                 |
   approved=true + rule_id + evidence_id
                 v
            DeviceExecutor
           /              \
    X5CameraAdapter     Link2Adapter
           |
    下载 .insp / .insv
           v
       IMediaProcessor
           |
 全景图片 / 图片序列 / 拼接视频
```

本包属于本地后端的设备控制与媒体处理模块。云端服务和 Agent 不加载厂商 DLL，也不直接发送相机指令。

## 各层职责

- `PlanValidator`：校验权限、参数范围、设备状态和 Skill 规则。
- `DeviceExecutor`：再次确认审批状态、路由设备动作并输出审计记录。
- `IDeviceAdapter`：隔离具体厂商 SDK，对外暴露统一能力。
- `IMediaProcessor`：管理离线拼接任务、进度、结果和取消操作。
- 数据存储层：管理输入输出路径，并持久化导演计划、证据和审计结果。

## 设备能力对应关系

| 项目能力 | X5 CameraSDK | Link 2 UVCCamera SDK | MediaSDK |
|---|---|---|---|
| 拍照、录像 | 支持 | 由主机UVC采集实现 | 不负责 |
| 实时画面 | CameraSDK实时流 | 标准UVC视频流 | X5实时拼接 |
| PTZ、跟踪、构图 | 不支持 | 支持 | 不负责 |
| 下载相机素材 | 支持 | 不适用 | 不负责 |
| 全景图片、视频处理 | 提供原始素材 | 不适用 | 支持 |
| 视频抽帧 | 提供原始素材 | 主机可以抓帧 | 支持 |

## Agent 接口约定

Agent 输出必须符合 `schemas/device_action.schema.json`。只有 `PlanValidator` 可以把 `approved` 设置为 `true`。

每次设备动作都必须携带：

- `request_id`：动作请求唯一标识。
- `device_id`：目标设备。
- `rule_id`：触发动作的 Skill 规则。
- `evidence_id`：触发动作的事件证据。
- `approved`：PlanValidator 审批结果。
- `parameters`：动作参数。

`DeviceExecutor` 会生成 `AuditRecord`，把实际执行结果连接到导演时间线。
