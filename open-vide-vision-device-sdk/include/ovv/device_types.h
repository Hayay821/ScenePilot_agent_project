#pragma once

#include <chrono>
#include <cstdint>
#include <string>
#include <vector>

namespace ovv {

enum class DeviceKind { x5, link2, mock };
enum class ActionType {
    capture_photo,
    start_recording,
    stop_recording,
    start_preview,
    stop_preview,
    download_media,
    set_tracking,
    set_composition,
    set_track_speed,
    set_ptz,
    set_zoom,
    set_privacy,
    shutdown
};
enum class Composition { none, head, half_body, full_body };
enum class TrackSpeed { fast, normal, slow };
enum class ErrorCode {
    ok,
    invalid_request,
    approval_required,
    device_not_found,
    not_connected,
    unsupported,
    vendor_error,
    busy,
    cancelled
};

struct DeviceInfo {
    std::string id;
    DeviceKind kind{DeviceKind::mock};
    std::string model;
    std::string serial;
    std::string firmware;
    std::vector<ActionType> capabilities;
};

struct DeviceAction {
    std::string request_id;
    std::string device_id;
    ActionType type{ActionType::capture_photo};
    bool approved{false};
    std::string evidence_id;
    std::string rule_id;

    std::string source_path;
    std::string destination_path;
    Composition composition{Composition::none};
    TrackSpeed track_speed{TrackSpeed::normal};
    double pan_degrees{0.0};
    double tilt_degrees{0.0};
    double zoom{1.0};
    bool enabled{false};
};

struct ActionResult {
    bool success{false};
    ErrorCode code{ErrorCode::vendor_error};
    std::string message;
    std::string output_uri;
};

struct AuditRecord {
    std::string request_id;
    std::string device_id;
    ActionType action{ActionType::capture_photo};
    std::string evidence_id;
    std::string rule_id;
    bool approved{false};
    ActionResult result;
    std::chrono::system_clock::time_point executed_at;
};

}  // namespace ovv

