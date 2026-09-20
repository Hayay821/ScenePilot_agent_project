/**
 * HTTP 服务器头文件
 *
 * 提供 RESTful API 接口
 */

#ifndef HTTP_SERVER_H
#define HTTP_SERVER_H

#include <string>
#include <memory>
#include <atomic>

// Forward declarations
class DeviceManager;

/**
 * HTTP 服务器
 *
 * 端点:
 * - GET /v1/capabilities
 * - POST /v1/commands
 * - GET /health
 */
class HttpServer {
public:
    HttpServer(int port, DeviceManager* device_manager);
    ~HttpServer();

    // 禁止复制
    HttpServer(const HttpServer&) = delete;
    HttpServer& operator=(const HttpServer&) = delete;

    void start();
    void stop();
    bool is_running() const;

private:
    int port_;
    DeviceManager* device_manager_;
    std::atomic<bool> running_;

    // 路由处理方法
    std::string handle_get_capabilities();
    std::string handle_post_commands(const std::string& body);
    std::string handle_health();

    // 命令执行
    std::string execute_command(const std::string& command_id,
                               const std::string& action,
                               const std::string& args_json);

    // 辅助方法
    std::string create_error_response(const std::string& error);
    std::string create_success_response(const std::string& data);
};

#endif // HTTP_SERVER_H
