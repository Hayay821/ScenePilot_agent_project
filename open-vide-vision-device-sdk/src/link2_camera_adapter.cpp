#include "ovv/device_adapter.h"
#include <uvc_camera.h>
#include <algorithm>
#include <cmath>
#include <memory>
#include <utility>
#include <vector>

namespace ovv {
namespace {
class Link2CameraAdapter final : public IDeviceAdapter {
public:
    explicit Link2CameraAdapter(std::string preferred_name) : preferred_name_(std::move(preferred_name)) {}

    ActionResult Connect() override {
        std::vector<UVCCameraInfo> cameras;
        uvc::GetUVCCameraList(cameras);
        auto camera = preferred_name_.empty() ? cameras.begin() :
            std::find_if(cameras.begin(), cameras.end(), [&](const auto& item) {
                return item.friendly_name.find(preferred_name_) != std::string::npos;
            });
        if (camera == cameras.end()) return {false, ErrorCode::device_not_found, "未发现 Link 2 设备", {}};

        controller_ = std::make_unique<uvc::UVCCameraController>(*camera);
        extended_controller_ = std::make_unique<uvc::UVCCameraExtendController>(*camera);
        std::string serial;
        extended_controller_->GetSerialNumber(serial);
        info_ = {"link2-" + (serial.empty() ? std::to_string(camera->video_device_index) : serial),
                 DeviceKind::link2, camera->friendly_name, serial, {},
                 {ActionType::set_tracking, ActionType::set_composition, ActionType::set_track_speed,
                  ActionType::set_ptz, ActionType::set_zoom, ActionType::set_privacy}};
        return {true, ErrorCode::ok, "Link 2 连接成功", {}};
    }

    void Disconnect() noexcept override { extended_controller_.reset(); controller_.reset(); }
    bool IsConnected() const noexcept override { return controller_ && extended_controller_; }
    DeviceInfo Info() const override { return info_; }
    bool Supports(ActionType action) const noexcept override {
        return std::find(info_.capabilities.begin(), info_.capabilities.end(), action) != info_.capabilities.end();
    }

    ActionResult Execute(const DeviceAction& action) override {
        if (!IsConnected()) return {false, ErrorCode::not_connected, "Link 2 尚未连接", {}};
        bool succeeded = false;
        switch (action.type) {
        case ActionType::set_tracking: {
            VideoModeAuxiliaryData auxiliary{};
            succeeded = extended_controller_->SetVideoMode(
                action.enabled ? VideoMode::AutoComposition : VideoMode::Normal, auxiliary);
            break;
        }
        case ActionType::set_composition: {
            auto style = CompositionStyle::None;
            if (action.composition == Composition::head) style = CompositionStyle::OnlyHead;
            if (action.composition == Composition::half_body) style = CompositionStyle::HalfBody;
            if (action.composition == Composition::full_body) style = CompositionStyle::FullBody;
            succeeded = extended_controller_->SetCompositionStyle(style);
            break;
        }
        case ActionType::set_track_speed: {
            auto speed = ::TrackSpeed::Normal;
            if (action.track_speed == ovv::TrackSpeed::fast) speed = ::TrackSpeed::Fast;
            if (action.track_speed == ovv::TrackSpeed::slow) speed = ::TrackSpeed::Slow;
            succeeded = extended_controller_->SetTrackSpeed(speed);
            break;
        }
        case ActionType::set_ptz:
            succeeded = controller_->SetPanTiltAbsolute(
                static_cast<long>(std::lround(action.pan_degrees * 360.0)),
                static_cast<long>(std::lround(action.tilt_degrees * 360.0)));
            break;
        case ActionType::set_zoom: {
            CameraControlInfo range{};
            if (controller_->GetZoomAbsoluteRange(range)) {
                const double ratio = std::clamp((action.zoom - 1.0) / 3.0, 0.0, 1.0);
                const auto value = static_cast<long>(std::lround(range.min + ratio * (range.max - range.min)));
                succeeded = controller_->SetZoomAbsolute(value);
            }
            break;
        }
        case ActionType::set_privacy:
            succeeded = extended_controller_->SetPrivacyMode(action.enabled);
            break;
        default:
            return {false, ErrorCode::unsupported, "Link 2 不支持该动作", {}};
        }
        return succeeded ? ActionResult{true, ErrorCode::ok, "Link 2 动作执行成功", {}} :
                           ActionResult{false, ErrorCode::vendor_error, "Link 2 SDK 拒绝了该动作", {}};
    }

private:
    std::string preferred_name_;
    DeviceInfo info_{"link2-pending", DeviceKind::link2, "Insta360 Link 2", {}, {}, {}};
    std::unique_ptr<uvc::UVCCameraController> controller_;
    std::unique_ptr<uvc::UVCCameraExtendController> extended_controller_;
};
}
std::shared_ptr<IDeviceAdapter> MakeLink2CameraAdapter(std::string preferred_name) {
    return std::make_shared<Link2CameraAdapter>(std::move(preferred_name));
}
}