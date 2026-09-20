/**
 * 协议数据类型定义
 *
 * 与 Python protocols 模块保持一致
 */

#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <string>
#include <map>
#include <vector>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

/**
 * 命令动作枚举
 */
namespace CommandAction {
    constexpr const char* SET_PAN_TILT_ABSOLUTE = "set_pan_tilt_absolute";
    constexpr const char* SET_PAN_TILT_RELATIVE = "set_pan_tilt_relative";
    constexpr const char* PTZ_STOP = "ptz_stop";
    constexpr const char* PTZ_HOME = "ptz_home";
    constexpr const char* START_TRACKING = "start_tracking";
    constexpr const char* STOP_TRACKING = "stop_tracking";
    constexpr const char* SET_TRACK_TARGET = "set_track_target";
    constexpr const char* SET_TRACK_SPEED = "set_track_speed";
    constexpr const char* SET_COMPOSITION_STYLE = "set_composition_style";
    constexpr const char* SET_VIDEO_MODE = "set_video_mode";
    constexpr const char* ENABLE_GESTURE = "enable_gesture";
    constexpr const char* DISABLE_GESTURE = "disable_gesture";
}

/**
 * 命令状态枚举
 */
namespace CommandStatus {
    constexpr const char* SUCCESS = "success";
    constexpr const char* FAILED = "failed";
    constexpr const char* TIMEOUT = "timeout";
    constexpr const char* UNSUPPORTED = "unsupported";
    constexpr const char* INVALID_ARGS = "invalid_args";
}

/**
 * 事件类型枚举
 */
namespace EventType {
    constexpr const char* CONNECTED = "connected";
    constexpr const char* DISCONNECTED = "disconnected";
    constexpr const char* CONNECTION_ERROR = "connection_error";
    constexpr const char* PTZ_POSITION_CHANGED = "ptz_position_changed";
    constexpr const char* PTZ_LIMIT_REACHED = "ptz_limit_reached";
    constexpr const char* TRACKING_STARTED = "tracking_started";
    constexpr const char* TRACKING_STOPPED = "tracking_stopped";
    constexpr const char* TARGET_LOST = "target_lost";
    constexpr const char* TARGET_ACQUIRED = "target_acquired";
    constexpr const char* GESTURE_DETECTED = "gesture_detected";
    constexpr const char* ERROR = "error";
    constexpr const char* WARNING = "warning";
    constexpr const char* INFO = "info";
}

/**
 * 设备命令
 */
struct DeviceCommand {
    std::string command_id;
    std::string action;
    json args;
    int deadline_ms = 1000;

    static DeviceCommand from_json(const json& j) {
        DeviceCommand cmd;
        cmd.command_id = j.value("command_id", "");
        cmd.action = j.value("action", "");
        cmd.args = j.value("args", json::object());
        cmd.deadline_ms = j.value("deadline_ms", 1000);
        return cmd;
    }
};

/**
 * 命令结果
 */
struct CommandResult {
    std::string command_id;
    std::string status;
    json result;
    std::string error;
    std::string timestamp;
    double execution_time_ms = 0.0;

    json to_json() const {
        json j;
        j["command_id"] = command_id;
        j["status"] = status;
        j["result"] = result.is_null() ? nullptr : result;
        j["error"] = error.empty() ? nullptr : error;
        j["timestamp"] = timestamp;
        j["execution_time_ms"] = execution_time_ms;
        return j;
    }
};

/**
 * 设备事件
 */
struct DeviceEvent {
    std::string event_id;
    std::string device_id;
    std::string event_type;
    std::string timestamp;
    json data;
    std::string severity = "info";
    std::string message;

    json to_json() const {
        json j;
        j["event_id"] = event_id;
        j["device_id"] = device_id;
        j["event_type"] = event_type;
        j["timestamp"] = timestamp;
        j["data"] = data;
        j["severity"] = severity;
        j["message"] = message;
        return j;
    }
};

/**
 * 辅助函数: 获取当前 ISO 8601 时间戳
 */
inline std::string get_iso_timestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;

    std::stringstream ss;
    ss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%S");
    ss << '.' << std::setfill('0') << std::setw(3) << ms.count() << 'Z';
    return ss.str();
}

#endif // PROTOCOL_H
