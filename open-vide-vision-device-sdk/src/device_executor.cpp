#include "ovv/device_executor.h"

#include <algorithm>
#include <utility>

namespace ovv {

DeviceExecutor::DeviceExecutor(AuditSink audit_sink) : audit_sink_(std::move(audit_sink)) {}

bool DeviceExecutor::Register(std::shared_ptr<IDeviceAdapter> adapter) {
    if (!adapter || adapter->Info().id.empty()) return false;
    const auto id = adapter->Info().id;
    std::lock_guard<std::mutex> lock(mutex_);
    return devices_.emplace(id, std::move(adapter)).second;
}

bool DeviceExecutor::Remove(const std::string& device_id) {
    std::shared_ptr<IDeviceAdapter> removed;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto it = devices_.find(device_id);
        if (it == devices_.end()) return false;
        removed = std::move(it->second);
        devices_.erase(it);
    }
    removed->Disconnect();
    return true;
}

std::vector<DeviceInfo> DeviceExecutor::ListDevices() const {
    std::vector<DeviceInfo> result;
    std::lock_guard<std::mutex> lock(mutex_);
    result.reserve(devices_.size());
    for (const auto& entry : devices_) result.push_back(entry.second->Info());
    return result;
}

ActionResult DeviceExecutor::Validate(const DeviceAction& action, const IDeviceAdapter& adapter) const {
    if (action.request_id.empty() || action.device_id.empty())
        return {false, ErrorCode::invalid_request, "必须提供 request_id 和 device_id", {}};
    if (!action.approved)
        return {false, ErrorCode::approval_required, "动作必须先通过 PlanValidator 审批", {}};
    if (!adapter.IsConnected())
        return {false, ErrorCode::not_connected, "设备尚未连接", {}};
    if (!adapter.Supports(action.type))
        return {false, ErrorCode::unsupported, "该设备不支持此动作", {}};
    if (action.type == ActionType::set_ptz &&
        (action.pan_degrees < -180.0 || action.pan_degrees > 180.0 ||
         action.tilt_degrees < -90.0 || action.tilt_degrees > 90.0))
        return {false, ErrorCode::invalid_request, "PTZ角度超出安全范围", {}};
    if (action.type == ActionType::set_zoom && (action.zoom < 1.0 || action.zoom > 4.0))
        return {false, ErrorCode::invalid_request, "变焦值必须位于 [1.0, 4.0] 范围内", {}};
    if (action.type == ActionType::download_media &&
        (action.source_path.empty() || action.destination_path.empty()))
        return {false, ErrorCode::invalid_request, "下载操作必须提供来源路径和目标路径", {}};
    return {true, ErrorCode::ok, "校验通过", {}};
}

ActionResult DeviceExecutor::Execute(const DeviceAction& action) {
    std::shared_ptr<IDeviceAdapter> adapter;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto it = devices_.find(action.device_id);
        if (it != devices_.end()) adapter = it->second;
    }
    if (!adapter) {
        ActionResult result{false, ErrorCode::device_not_found, "设备尚未注册", {}};
        Audit(action, result);
        return result;
    }
    auto result = Validate(action, *adapter);
    if (result.success) result = adapter->Execute(action);
    Audit(action, result);
    return result;
}

void DeviceExecutor::Audit(const DeviceAction& action, const ActionResult& result) const {
    if (!audit_sink_) return;
    audit_sink_({action.request_id, action.device_id, action.type, action.evidence_id,
                 action.rule_id, action.approved, result, std::chrono::system_clock::now()});
}

}  // namespace ovv





