#include "ovv/device_adapter.h"
#include <camera/camera.h>
#include <camera/device_discovery.h>
#include <algorithm>
#include <memory>
#include <utility>
namespace ovv { namespace {
class X5 final : public IDeviceAdapter {
 public:
  explicit X5(std::string serial): wanted_(std::move(serial)) {}
  ActionResult Connect() override {
    ins_camera::DeviceDiscovery discovery; auto devices=discovery.GetAvailableDevices();
    auto it=wanted_.empty()?devices.begin():std::find_if(devices.begin(),devices.end(),[&](const auto& d){return d.serial_number==wanted_;});
    if(it==devices.end()){discovery.FreeDeviceDescriptors(devices);return {false,ErrorCode::device_not_found,"X5 not found",{}};}
    info_={"x5-"+it->serial_number,DeviceKind::x5,it->camera_name,it->serial_number,it->fw_version,{ActionType::capture_photo,ActionType::start_recording,ActionType::stop_recording,ActionType::start_preview,ActionType::stop_preview,ActionType::download_media,ActionType::shutdown}};
    camera_=std::make_shared<ins_camera::Camera>(it->info); bool ok=camera_->Open(); discovery.FreeDeviceDescriptors(devices);
    if(!ok){camera_.reset();return {false,ErrorCode::vendor_error,"Camera::Open failed",{}};} return {true,ErrorCode::ok,"X5 connected",{}};
  }
  void Disconnect() noexcept override {if(camera_)camera_->Close();camera_.reset();}
  bool IsConnected() const noexcept override {return camera_&&camera_->IsConnected();}
  DeviceInfo Info() const override{return info_;}
  bool Supports(ActionType a) const noexcept override{return std::find(info_.capabilities.begin(),info_.capabilities.end(),a)!=info_.capabilities.end();}
  ActionResult Execute(const DeviceAction& a) override {
    if(!camera_)return {false,ErrorCode::not_connected,"X5 not connected",{}};
    switch(a.type){
      case ActionType::capture_photo:{auto m=camera_->TakePhoto();return m.Empty()?ActionResult{false,ErrorCode::vendor_error,"TakePhoto failed",{}}:ActionResult{true,ErrorCode::ok,"photo captured",m.GetSingleOrigin()};}
      case ActionType::start_recording:{bool ok=camera_->StartRecording();return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,"start recording",{}};}
      case ActionType::stop_recording:{auto m=camera_->StopRecording();return m.Empty()?ActionResult{false,ErrorCode::vendor_error,"StopRecording failed",{}}:ActionResult{true,ErrorCode::ok,"recording stopped",m.GetSingleOrigin()};}
      case ActionType::start_preview:{ins_camera::LiveStreamParam p;p.video_resolution=ins_camera::VideoResolution::RES_1440_720P30;p.lrv_video_resulution=p.video_resolution;p.video_bitrate=524288;p.enable_audio=false;p.using_lrv=false;bool ok=camera_->StartLiveStreaming(p);return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,"start preview",{}};}
      case ActionType::stop_preview:{bool ok=camera_->StopLiveStreaming();return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,"stop preview",{}};}
      case ActionType::download_media:{bool ok=camera_->DownloadCameraFile(a.source_path,a.destination_path);return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,"download",a.destination_path};}
      case ActionType::shutdown:{bool ok=camera_->ShutdownCamera();return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,"shutdown",{}};}
      default:return {false,ErrorCode::unsupported,"unsupported X5 action",{}};
    }
  }
 private: std::string wanted_; DeviceInfo info_{"x5-pending",DeviceKind::x5,"Insta360 X5",{},{},{}}; std::shared_ptr<ins_camera::Camera> camera_;
}; }
std::shared_ptr<IDeviceAdapter> MakeX5CameraAdapter(std::string serial){return std::make_shared<X5>(std::move(serial));}
}
