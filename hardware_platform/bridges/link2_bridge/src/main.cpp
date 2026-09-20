/**
 * Link 2 Bridge - 主程序入口
 *
 * 基于 Link-SDK 创建 HTTP/WebSocket 服务，提供统一设备控制接口
 */

#include <iostream>
#include <string>
#include <csignal>
#include <memory>
#include <thread>
#include <chrono>

#include "device_manager.h"
#include "http_server.h"
#include "websocket_server.h"

// 全局变量用于信号处理
static bool g_running = true;
static std::unique_ptr<DeviceManager> g_device_manager;
static std::unique_ptr<HttpServer> g_http_server;
static std::unique_ptr<WebSocketServer> g_websocket_server;

/**
 * 信号处理函数
 */
void signal_handler(int signal) {
    if (signal == SIGINT || signal == SIGTERM) {
        std::cout << "\n[INFO] Received shutdown signal, cleaning up...\n";
        g_running = false;

        // 发送 PTZ Stop 确保安全
        if (g_device_manager && g_device_manager->is_connected()) {
            std::cout << "[INFO] Sending PTZ Stop before exit\n";
            g_device_manager->ptz_stop();
        }
    }
}

/**
 * 打印帮助信息
 */
void print_usage(const char* program_name) {
    std::cout << "Link 2 Bridge - UVC Camera SDK Integration\n\n";
    std::cout << "Usage: " << program_name << " [options]\n\n";
    std::cout << "Options:\n";
    std::cout << "  --port PORT         HTTP server port (default: 8002)\n";
    std::cout << "  --ws-port PORT      WebSocket server port (default: 8003)\n";
    std::cout << "  --device-index N    Device index if multiple cameras (default: 0)\n";
    std::cout << "  --log-level LEVEL   Log level: debug/info/warning/error (default: info)\n";
    std::cout << "  --help              Show this help message\n\n";
    std::cout << "Example:\n";
    std::cout << "  " << program_name << " --port 8002 --log-level debug\n\n";
}

/**
 * 解析命令行参数
 */
struct Config {
    int http_port = 8002;
    int ws_port = 8003;
    int device_index = 0;
    std::string log_level = "info";
};

Config parse_args(int argc, char* argv[]) {
    Config config;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            exit(0);
        }
        else if (arg == "--port" && i + 1 < argc) {
            config.http_port = std::stoi(argv[++i]);
        }
        else if (arg == "--ws-port" && i + 1 < argc) {
            config.ws_port = std::stoi(argv[++i]);
        }
        else if (arg == "--device-index" && i + 1 < argc) {
            config.device_index = std::stoi(argv[++i]);
        }
        else if (arg == "--log-level" && i + 1 < argc) {
            config.log_level = argv[++i];
        }
        else {
            std::cerr << "[ERROR] Unknown argument: " << arg << "\n";
            print_usage(argv[0]);
            exit(1);
        }
    }

    return config;
}

/**
 * 主函数
 */
int main(int argc, char* argv[]) {
    std::cout << "==========================================\n";
    std::cout << "Link 2 Bridge - Starting\n";
    std::cout << "==========================================\n";

    // 解析参数
    Config config = parse_args(argc, argv);

    std::cout << "[INFO] Configuration:\n";
    std::cout << "  HTTP Port: " << config.http_port << "\n";
    std::cout << "  WebSocket Port: " << config.ws_port << "\n";
    std::cout << "  Device Index: " << config.device_index << "\n";
    std::cout << "  Log Level: " << config.log_level << "\n";
    std::cout << "==========================================\n";

    // 注册信号处理
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    try {
        // 初始化设备管理器
        std::cout << "[INFO] Initializing Device Manager...\n";
        g_device_manager = std::make_unique<DeviceManager>(config.device_index);

        if (!g_device_manager->enumerate_devices()) {
            std::cerr << "[ERROR] No Link 2 devices found\n";
            return 1;
        }

        if (!g_device_manager->connect()) {
            std::cerr << "[ERROR] Failed to connect to device\n";
            return 1;
        }

        std::cout << "[INFO] Device connected: " << g_device_manager->get_device_id() << "\n";

        // 初始化 HTTP 服务器
        std::cout << "[INFO] Starting HTTP server on port " << config.http_port << "...\n";
        g_http_server = std::make_unique<HttpServer>(config.http_port, g_device_manager.get());

        std::thread http_thread([&]() {
            g_http_server->start();
        });

        // 初始化 WebSocket 服务器
        std::cout << "[INFO] Starting WebSocket server on port " << config.ws_port << "...\n";
        g_websocket_server = std::make_unique<WebSocketServer>(config.ws_port, g_device_manager.get());

        std::thread ws_thread([&]() {
            g_websocket_server->start();
        });

        std::cout << "==========================================\n";
        std::cout << "[INFO] Link 2 Bridge is running\n";
        std::cout << "[INFO] HTTP API: http://localhost:" << config.http_port << "\n";
        std::cout << "[INFO] WebSocket: ws://localhost:" << config.ws_port << "/v1/events\n";
        std::cout << "[INFO] Press Ctrl+C to stop\n";
        std::cout << "==========================================\n";

        // 主循环
        while (g_running) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        // 清理
        std::cout << "[INFO] Shutting down servers...\n";

        if (g_http_server) {
            g_http_server->stop();
        }

        if (g_websocket_server) {
            g_websocket_server->stop();
        }

        if (http_thread.joinable()) {
            http_thread.join();
        }

        if (ws_thread.joinable()) {
            ws_thread.join();
        }

        if (g_device_manager) {
            g_device_manager->disconnect();
        }

        std::cout << "[INFO] Link 2 Bridge stopped\n";
        std::cout << "==========================================\n";

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Fatal error: " << e.what() << "\n";
        return 1;
    }
}
