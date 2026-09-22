#include "ovv/device_executor.h"

#include <cassert>
#include <iostream>

int main() {
    ovv::DeviceInfo link{"link2-main", ovv::DeviceKind::mock, "Insta360 Link 2", "MOCK-LINK2", "1",
                         {ovv::ActionType::set_ptz, ovv::ActionType::set_composition}};
    auto adapter = ovv::MakeMockDeviceAdapter(link);
    assert(adapter->Connect().success);

    int audit_count = 0;
    ovv::DeviceExecutor executor([&](const ovv::AuditRecord&) { ++audit_count; });
    assert(executor.Register(adapter));

    ovv::DeviceAction denied{"r1", "link2-main", ovv::ActionType::set_ptz};
    assert(executor.Execute(denied).code == ovv::ErrorCode::approval_required);

    ovv::DeviceAction unsafe{"r2", "link2-main", ovv::ActionType::set_ptz};
    unsafe.approved = true;
    unsafe.pan_degrees = 181.0;
    assert(executor.Execute(unsafe).code == ovv::ErrorCode::invalid_request);

    ovv::DeviceAction valid{"r3", "link2-main", ovv::ActionType::set_composition};
    valid.approved = true;
    valid.composition = ovv::Composition::full_body;
    assert(executor.Execute(valid).success);
    assert(audit_count == 3);

    std::cout << "设备执行器测试通过\n";
    return 0;
}


