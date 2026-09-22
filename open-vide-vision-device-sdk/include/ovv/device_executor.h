#pragma once

#include "ovv/device_adapter.h"

#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace ovv {

class DeviceExecutor {
public:
    using AuditSink = std::function<void(const AuditRecord&)>;

    explicit DeviceExecutor(AuditSink audit_sink = {});
    bool Register(std::shared_ptr<IDeviceAdapter> adapter);
    bool Remove(const std::string& device_id);
    std::vector<DeviceInfo> ListDevices() const;
    ActionResult Execute(const DeviceAction& action);

private:
    ActionResult Validate(const DeviceAction& action, const IDeviceAdapter& adapter) const;
    void Audit(const DeviceAction& action, const ActionResult& result) const;

    mutable std::mutex mutex_;
    std::unordered_map<std::string, std::shared_ptr<IDeviceAdapter>> devices_;
    AuditSink audit_sink_;
};

}  // namespace ovv

