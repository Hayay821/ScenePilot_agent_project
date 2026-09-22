#pragma once

#include "ovv/device_types.h"

#include <memory>
#include <string>

namespace ovv {

class IDeviceAdapter {
public:
    virtual ~IDeviceAdapter() = default;
    virtual ActionResult Connect() = 0;
    virtual void Disconnect() noexcept = 0;
    virtual bool IsConnected() const noexcept = 0;
    virtual DeviceInfo Info() const = 0;
    virtual bool Supports(ActionType action) const noexcept = 0;
    virtual ActionResult Execute(const DeviceAction& action) = 0;
};

std::shared_ptr<IDeviceAdapter> MakeMockDeviceAdapter(DeviceInfo info);

#ifdef OVV_ENABLE_X5_CAMERA
std::shared_ptr<IDeviceAdapter> MakeX5CameraAdapter(std::string preferred_serial = {});
#endif

#ifdef OVV_ENABLE_LINK_UVC
std::shared_ptr<IDeviceAdapter> MakeLink2CameraAdapter(std::string preferred_name = {});
#endif

}  // namespace ovv

