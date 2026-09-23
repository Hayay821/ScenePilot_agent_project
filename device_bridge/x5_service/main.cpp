#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include "ovv/device_adapter.h"
#include "ovv/device_executor.h"
#include <camera/camera.h>
#include <atomic>
#include <cstdlib>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <mutex>
#include <thread>

#pragma comment(lib, "Ws2_32.lib")

namespace {
struct RegisteredDevice {
    std::shared_ptr<ovv::IDeviceAdapter> adapter;
    std::string executor_id;
};
std::unordered_map<std::string, RegisteredDevice> devices;
std::unordered_set<std::string> connecting_devices;
std::mutex devices_mutex;
ovv::DeviceExecutor executor;
std::atomic<bool> x5_previewing{false};

std::string escape(const std::string& s){std::string o;for(char c:s){if(c=='"'||c=='\\')o+='\\';if(c=='\n'){o+="\\n";continue;}o+=c;}return o;}
std::string field(const std::string& body,const std::string& name){
    auto p=body.find("\""+name+"\"");if(p==std::string::npos)return{};p=body.find(':',p);if(p==std::string::npos)return{};
    p=body.find('"',p);if(p==std::string::npos)return{};auto e=body.find('"',p+1);
    return e==std::string::npos?std::string{}:body.substr(p+1,e-p-1);
}
bool boolean(const std::string& body,const std::string& name){
    auto p=body.find("\""+name+"\"");if(p==std::string::npos)return false;p=body.find(':',p);
    if(p==std::string::npos)return false;auto end=body.find_first_of(",}",p);auto value=body.find("true",p);
    return value!=std::string::npos&&(end==std::string::npos||value<end);
}
double number(const std::string& body,const std::string& name,double fallback){
    auto p=body.find("\""+name+"\"");if(p==std::string::npos)return fallback;p=body.find(':',p);
    if(p==std::string::npos)return fallback;char* end=nullptr;double v=std::strtod(body.c_str()+p+1,&end);
    return end==body.c_str()+p+1?fallback:v;
}
std::string json_result(const ovv::ActionResult& r){
    return "{\"success\":"+std::string(r.success?"true":"false")+",\"message\":\""+escape(r.message)+"\",\"output_uri\":\""+escape(r.output_uri)+"\"}";
}
void reply(SOCKET client,int status,const std::string& body,const char* type="application/json; charset=utf-8"){
    std::ostringstream out;out<<"HTTP/1.1 "<<status<<(status==200?" OK":" Error")
        <<"\r\nContent-Type: "<<type
        <<"\r\nAccess-Control-Allow-Origin: *"
        <<"\r\nAccess-Control-Allow-Headers: Content-Type"
        <<"\r\nAccess-Control-Allow-Methods: GET, POST, OPTIONS"
        <<"\r\nCache-Control: no-store"
        <<"\r\nContent-Length: "<<body.size()<<"\r\nConnection: close\r\n\r\n"<<body;
    auto value=out.str();send(client,value.data(),static_cast<int>(value.size()),0);
}
bool parse_action(const std::string& name,ovv::ActionType& type){
    static const std::unordered_map<std::string,ovv::ActionType> actions={
        {"capture_photo",ovv::ActionType::capture_photo},{"start_recording",ovv::ActionType::start_recording},
        {"stop_recording",ovv::ActionType::stop_recording},{"start_preview",ovv::ActionType::start_preview},
        {"stop_preview",ovv::ActionType::stop_preview},{"download_media",ovv::ActionType::download_media},
        {"set_tracking",ovv::ActionType::set_tracking},{"set_composition",ovv::ActionType::set_composition},
        {"set_track_speed",ovv::ActionType::set_track_speed},{"set_ptz",ovv::ActionType::set_ptz},
        {"set_zoom",ovv::ActionType::set_zoom},{"set_privacy",ovv::ActionType::set_privacy},
        {"shutdown",ovv::ActionType::shutdown}};
    auto it=actions.find(name);if(it==actions.end())return false;type=it->second;return true;
}
std::string device_json(const std::string& alias,const std::string& fallback_model){
    std::shared_ptr<ovv::IDeviceAdapter> adapter;
    bool connecting=false;
    {
        std::lock_guard<std::mutex> lock(devices_mutex);
        auto it=devices.find(alias);
        if(it!=devices.end())adapter=it->second.adapter;
        connecting=connecting_devices.count(alias)>0;
    }
    bool connected=adapter&&adapter->IsConnected();
    ovv::DeviceInfo info;if(connected)info=adapter->Info();
    return "{\"id\":\""+alias+"\",\"model\":\""+escape(connected?info.model:fallback_model)+
        "\",\"serial\":\""+escape(connected?info.serial:"")+"\",\"firmware\":\""+
        escape(connected?info.firmware:"")+"\",\"connected\":"+(connected?"true":"false")+
        ",\"connecting\":"+(connecting?"true":"false")+"}";
}
std::shared_ptr<ovv::IDeviceAdapter> make_adapter(const std::string& alias){
    if(alias=="x5-main")return ovv::MakeX5CameraAdapter();
    if(alias=="link2-main")return ovv::MakeLink2CameraAdapter("Insta360 Link");
    return {};
}
void connect_device(SOCKET client,const std::string& alias){
    {
        std::lock_guard<std::mutex> lock(devices_mutex);
        auto existing=devices.find(alias);
        if(existing!=devices.end()&&existing->second.adapter->IsConnected()){
            reply(client,200,"{\"success\":true,\"message\":\"设备已连接\"}");return;
        }
        if(connecting_devices.count(alias)){
            reply(client,409,"{\"success\":false,\"message\":\"设备正在连接，请勿重复点击\"}");return;
        }
        connecting_devices.insert(alias);
    }
    auto adapter=make_adapter(alias);
    ovv::ActionResult result;
    if(!adapter)result={false,ovv::ErrorCode::device_not_found,"设备不存在",{}};
    else result=adapter->Connect();
    if(result.success){
        auto real_id=adapter->Info().id;
        if(!executor.Register(adapter))result={false,ovv::ErrorCode::busy,"设备已经注册，请先断开后重试",{}};
        else {
            std::lock_guard<std::mutex> lock(devices_mutex);
            devices[alias]={adapter,real_id};
        }
    }
    {
        std::lock_guard<std::mutex> lock(devices_mutex);
        connecting_devices.erase(alias);
    }
    reply(client,result.success?200:503,json_result(result));
}
void handle(SOCKET client){
    std::string req;
    char buffer[16384];
    size_t expected_size=0;
    for(;;){
        int n=recv(client,buffer,sizeof(buffer),0);
        if(n<=0)return;
        req.append(buffer,n);
        auto headers=req.find("\r\n\r\n");
        if(headers==std::string::npos)continue;
        if(expected_size==0){
            auto marker=req.find("Content-Length:");
            size_t content_length=0;
            if(marker!=std::string::npos)content_length=static_cast<size_t>(std::strtoull(req.c_str()+marker+15,nullptr,10));
            expected_size=headers+4+content_length;
        }
        if(req.size()>=expected_size)break;
    }
    auto first_end=req.find("\r\n");auto first=req.substr(0,first_end);std::istringstream line(first);
    std::string method,path;line>>method>>path;auto query=path.find('?');if(query!=std::string::npos)path.resize(query);
    auto header_end=req.find("\r\n\r\n");std::string body=header_end==std::string::npos?"":req.substr(header_end+4);
    if(method=="OPTIONS"){reply(client,200,"{}");return;}
    if(method=="GET"&&path=="/api/v1/health"){reply(client,200,"{\"ok\":true,\"mode\":\"real-device-sdk\"}");return;}
    if(method=="GET"&&path=="/api/v1/devices"){
        reply(client,200,"["+device_json("x5-main","Insta360 X5")+","+device_json("link2-main","Insta360 Link 2")+"]");return;
    }
    const std::string prefix="/api/v1/devices/",suffix="/connect",disconnect_suffix="/disconnect";
    if(method=="POST"&&path.rfind(prefix,0)==0&&path.size()>prefix.size()+disconnect_suffix.size()&&path.substr(path.size()-disconnect_suffix.size())==disconnect_suffix){
        auto alias=path.substr(prefix.size(),path.size()-prefix.size()-disconnect_suffix.size());
        RegisteredDevice removed;
        {
            std::lock_guard<std::mutex> lock(devices_mutex);
            auto it=devices.find(alias);
            if(it==devices.end()){reply(client,200,"{\"success\":true,\"message\":\"设备已经断开\"}");return;}
            removed=it->second;
            devices.erase(it);
        }
        if(alias=="x5-main")x5_previewing=false;
        executor.Remove(removed.executor_id);
        reply(client,200,"{\"success\":true,\"message\":\"设备已断开连接\"}");return;
    }
    if(method=="POST"&&path.rfind(prefix,0)==0&&path.size()>prefix.size()+suffix.size()&&path.substr(path.size()-suffix.size())==suffix){
        connect_device(client,path.substr(prefix.size(),path.size()-prefix.size()-suffix.size()));return;
    }
    if(method=="GET"&&path=="/api/v1/assets"){
        std::string body="[";
        const char* configured=std::getenv("OVV_ASSET_DIR");
        if(configured&&*configured){
            std::error_code error;
            bool first=true;
            for(const auto& entry:std::filesystem::directory_iterator(configured,error)){
                if(!entry.is_regular_file())continue;
                if(!first)body+=",";
                first=false;
                auto name=entry.path().filename().u8string();
                body+="{\"name\":\""+escape(name)+"\",\"url\":\"assets/captures/"+escape(name)+"\",\"size\":"+std::to_string(entry.file_size())+"}";
            }
        }
        body+="]";
        reply(client,200,body);return;
    }
    if(method=="POST"&&path=="/api/v1/assets/link2-video"){
        const char* configured=std::getenv("OVV_ASSET_DIR");
        if(!configured||!*configured){reply(client,500,"{\"success\":false,\"message\":\"素材目录未配置\"}");return;}
        std::filesystem::create_directories(configured);
        auto stamp=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        auto name="link2_"+std::to_string(stamp)+".webm";
        std::filesystem::path destination=std::filesystem::path(configured)/name;
        std::ofstream output(destination,std::ios::binary);
        output.write(body.data(),static_cast<std::streamsize>(body.size()));
        output.close();
        if(!output){reply(client,500,"{\"success\":false,\"message\":\"保存 Link 2 视频失败\"}");return;}
        reply(client,200,"{\"success\":true,\"message\":\"Link 2 视频已保存到项目素材库\",\"output_uri\":\"assets/captures/"+name+"\"}");return;
    }
    if(method=="POST"&&path=="/api/v1/assets/link2-snapshot"){
        const char* configured=std::getenv("OVV_ASSET_DIR");
        if(!configured||!*configured){reply(client,500,"{\"success\":false,\"message\":\"素材目录未配置\"}");return;}
        std::filesystem::create_directories(configured);
        auto stamp=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
        auto name="link2_"+std::to_string(stamp)+".jpg";
        std::filesystem::path destination=std::filesystem::path(configured)/name;
        std::ofstream output(destination,std::ios::binary);
        output.write(body.data(),static_cast<std::streamsize>(body.size()));
        output.close();
        if(!output){reply(client,500,"{\"success\":false,\"message\":\"保存 Link 2 截图失败\"}");return;}
        reply(client,200,"{\"success\":true,\"message\":\"Link 2 图片已保存到项目素材库\",\"output_uri\":\"assets/captures/"+name+"\"}");return;
    }
    if(method=="POST"&&path=="/api/v1/device-actions/execute"){
        const auto alias=field(body,"device_id");
        RegisteredDevice registered;
        {
            std::lock_guard<std::mutex> lock(devices_mutex);
            auto it=devices.find(alias);
            if(it==devices.end()||!it->second.adapter->IsConnected()){
                reply(client,503,"{\"success\":false,\"message\":\"请先连接设备\"}");return;
            }
            registered=it->second;
        }
        const auto action_name=field(body,"action");ovv::ActionType type;
        if(!parse_action(action_name,type)){reply(client,400,"{\"success\":false,\"message\":\"未知设备动作\"}");return;}
        ovv::DeviceAction action;action.request_id=field(body,"request_id");action.device_id=registered.executor_id;
        action.type=type;action.approved=boolean(body,"approved");action.rule_id=field(body,"rule_id");
        action.evidence_id=field(body,"evidence_id");action.source_path=field(body,"source_path");
        action.destination_path=field(body,"destination_path");action.enabled=boolean(body,"enabled");
        action.zoom=number(body,"zoom",1.0);action.pan_degrees=number(body,"pan_degrees",0.0);
        action.tilt_degrees=number(body,"tilt_degrees",0.0);
        auto composition=field(body,"composition");
        if(composition=="head")action.composition=ovv::Composition::head;
        else if(composition=="half_body")action.composition=ovv::Composition::half_body;
        else if(composition=="full_body")action.composition=ovv::Composition::full_body;
        auto speed=field(body,"track_speed");
        if(speed=="fast")action.track_speed=ovv::TrackSpeed::fast;
        else if(speed=="slow")action.track_speed=ovv::TrackSpeed::slow;
        auto result=executor.Execute(action);
        if(alias=="x5-main"&&result.success&&action_name=="start_preview")x5_previewing=true;
        if(alias=="x5-main"&&action_name=="stop_preview")x5_previewing=false;
        reply(client,result.success?200:400,json_result(result));return;
    }
    if(method=="GET"&&path=="/api/v1/streams/x5-main.jpg"){
        if(!x5_previewing){reply(client,409,"{\"success\":false,\"message\":\"X5实时预览尚未启动\"}");return;}
        std::ifstream frame("preview/x5_latest.jpg",std::ios::binary);
        if(!frame){reply(client,404,"{\"success\":false,\"message\":\"全景帧尚未就绪\"}");return;}
        std::string bytes((std::istreambuf_iterator<char>(frame)),std::istreambuf_iterator<char>());
        reply(client,200,bytes,"image/jpeg");return;
    }
    reply(client,404,"{\"error\":\"接口不存在\"}");
}
}
int main(){
    DeleteFileW(L"preview\\x5_latest.jpg");
    SetConsoleOutputCP(65001);ins_camera::SetLogPath("logs");ins_camera::SetLogLevel(ins_camera::LogLevel::INFO);
    WSADATA data;if(WSAStartup(MAKEWORD(2,2),&data)!=0)return 1;
    SOCKET server=socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);sockaddr_in addr{};addr.sin_family=AF_INET;
    addr.sin_port=htons(8766);inet_pton(AF_INET,"127.0.0.1",&addr.sin_addr);
    if(bind(server,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))==SOCKET_ERROR){std::cerr<<"8766 端口被占用\n";return 2;}
    listen(server,SOMAXCONN);std::cout<<"真实设备服务：http://127.0.0.1:8766\n";
    for(;;){SOCKET client=accept(server,nullptr,nullptr);if(client!=INVALID_SOCKET){handle(client);closesocket(client);}}
}