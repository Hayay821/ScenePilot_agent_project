/**
 * 设备管理器头文件
 *
 * 封装 Link-SDK，提供设备枚举、连接、控制接口
 */

#ifndef DEVICE_MANAGER_H
#define DEVICE_MANAGER_H

#include <string>
#include <vector>
#include <memory>
#include <mutex>

// TODO: 包含 Link-SDK 头文件
// #include "UVCCameraSDK.h"

/**
 * 设备信息
 */
struct DeviceInfo {
    std::string device_id;
    std::string serial_number;
    std::string firmware_version;
    int pid;
    int vid;
};

/**
 * 设备能力
 */
struct DeviceCapabilities {
    std::vector<std::pair<int, int>> resolutions;  // (width, height)
    std::vector<int> frame_rates;
    std::vector<std::string> formats;

    // PTZ 能力
    double pan_min = -145.0;
    double pan_max = 145.0;
    double tilt_min = -45.0;
    double tilt_max = 90.0;

    // 追踪能力
    bool tracking_supported = false;
    bool target_selection_supported = false;
    std::vector<std::string> track_speeds;
    std::vector<std::string> composition_styles;

    // 其他能力
    bool gesture_supported = false;
    bool audio_supported = false;
};

/**
 * 设备管理器
 */
class DeviceManager {
public:
    explicit DeviceManager(int device_index = 0);
    ~DeviceManager();

    // 禁止复制
    DeviceManager(const DeviceManager&) = delete;
    DeviceManager& operator=(const DeviceManager&) = delete;

    // === 设备生命周期 ===

    bool enumerate_devices();
    bool connect();
    bool disconnect();
    bool is_connected() const;

    // === 设备信息 ===

    std::string get_device_id() const;
    DeviceInfo get_device_info() const;
    DeviceCapabilities get_capabilities() const;

    // === PTZ 控制 ===

    bool set_pan_tilt_absolute(double pan_deg, double tilt_deg);
    bool ptz_stop();
    bool ptz_home();

    // === 追踪控制 ===

    bool start_tracking(const std::string& target_id = "");
    bool stop_tracking();
    bool set_track_target(const std::string& target_id);
    bool set_track_speed(const std::string& speed);
    bool set_composition_style(const std::string& style);

    // === 视频模式 ===

    bool set_video_mode(const std::string& mode);

    // === 手势控制 ===

    bool enable_gesture();
    bool disable_gesture();

    // === 其他 ===

    std::vector<std::string> get_available_devices() const;

private:
    int device_index_;
    bool connected_;

    DeviceInfo device_info_;
    DeviceCapabilities capabilities_;

    // TODO: Link-SDK 设备句柄
    // UVCCamera* camera_;
    // UVCCameraController* controller_;
    // UVCCameraExtendController* extend_controller_;

    mutable std::mutex mutex_;

    // 内部辅助方法
    void query_device_info();
    void query_capabilities();
    bool validate_pan_tilt(double pan_deg, double tilt_deg) const;
};

#endif // DEVICE_MANAGER_H
