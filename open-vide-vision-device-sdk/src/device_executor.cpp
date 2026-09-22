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
        return {false, ErrorCode::invalid_request, "request_id and device_id are required", {}};
    if (!action.approved)
        return {false, ErrorCode::approval_required, "PlanValidator approval is required", {}};
    if (!adapter.IsConnected())
        return {false, ErrorCode::not_connected, "device is not connected", {}};
    if (!adapter.Supports(action.type))
        return {false, ErrorCode::unsupported, "action is not supported by this device", {}};
    if (action.type == ActionType::set_ptz &&
        (action.pan_degrees < -180.0 || action.pan_degrees > 180.0 ||
         action.tilt_degrees < -90.0 || action.tilt_degrees > 90.0))
        return {false, ErrorCode::invalid_request, "PTZ angle is outside the safety envelope", {}};
    if (action.type == ActionType::set_zoom && (action.zoom < 1.0 || action.zoom > 4.0))
        return {false, ErrorCode::invalid_request, "zoom must be in [1.0, 4.0]", {}};
    if (action.type == ActionType::download_media &&
        (action.source_path.empty() || action.destination_path.empty()))
        return {false, ErrorCode::invalid_request, "download source and destination are required", {}};
    return {true, ErrorCode::ok, "validated", {}};
}

ActionResult DeviceExecutor::Execute(const DeviceAction& action) {
    std::shared_ptr<IDeviceAdapter> adapter;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto it = devices_.find(action.device_id);
        if (it != devices_.end()) adapter = it->second;
    }
    if (!adapter) {
        ActionResult result{false, ErrorCode::device_not_found, "device is not registered", {}};
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



