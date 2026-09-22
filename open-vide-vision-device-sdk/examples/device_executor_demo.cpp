#include "ovv/device_executor.h"
#include "ovv/media_processor.h"

#include <iostream>

int main() {
    ovv::DeviceInfo x5{"x5-main", ovv::DeviceKind::mock, "Insta360 X5", "MOCK-X5", "2.2.0",
                       {ovv::ActionType::capture_photo, ovv::ActionType::start_recording,
                        ovv::ActionType::stop_recording, ovv::ActionType::download_media}};
    auto camera = ovv::MakeMockDeviceAdapter(x5);
    camera->Connect();

    ovv::DeviceExecutor executor([](const ovv::AuditRecord& record) {
        std::cout << "审计请求=" << record.request_id
                  << "，成功=" << record.result.success << '\n';
    });
    executor.Register(camera);

    ovv::DeviceAction action;
    action.request_id = "action-001";
    action.device_id = "x5-main";
    action.type = ovv::ActionType::capture_photo;
    action.approved = true;
    action.rule_id = "ActionCoach.peak";
    action.evidence_id = "event-143214";
    const auto result = executor.Execute(action);
    std::cout << result.message << "，输出=" << result.output_uri << '\n';

    auto media = ovv::MakeMockMediaProcessor();
    ovv::StitchRequest stitch{"stitch-001", {result.output_uri}, "output/panorama.jpg"};
    const auto job = media->Submit(stitch);
    std::cout << "拼接进度=" << job.progress << "%，输出=" << job.output << '\n';
    return result.success ? 0 : 1;
}



