#include "ovv/device_adapter.h"

#include <algorithm>
#include <utility>

namespace ovv {
namespace {

class MockDeviceAdapter final : public IDeviceAdapter {
public:
    explicit MockDeviceAdapter(DeviceInfo info) : info_(std::move(info)) {}
    ActionResult Connect() override {
        connected_ = true;
        return {true, ErrorCode::ok, "模拟设备已连接", {}};
    }
    void Disconnect() noexcept override { connected_ = false; }
    bool IsConnected() const noexcept override { return connected_; }
    DeviceInfo Info() const override { return info_; }
    bool Supports(ActionType action) const noexcept override {
        return std::find(info_.capabilities.begin(), info_.capabilities.end(), action) != info_.capabilities.end();
    }
    ActionResult Execute(const DeviceAction& action) override {
        std::string output;
        if (action.type == ActionType::capture_photo) output = "mock://media/photo.insp";
        if (action.type == ActionType::stop_recording) output = "mock://media/video.insv";
        return {true, ErrorCode::ok, "模拟动作执行成功", output};
    }
private:
    DeviceInfo info_;
    bool connected_{false};
};

}  // namespace

std::shared_ptr<IDeviceAdapter> MakeMockDeviceAdapter(DeviceInfo info) {
    return std::make_shared<MockDeviceAdapter>(std::move(info));
}

}  // namespace ovv


