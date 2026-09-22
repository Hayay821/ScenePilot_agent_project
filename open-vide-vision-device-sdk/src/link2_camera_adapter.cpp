#include "ovv/device_adapter.h"
#include <uvc_camera.h>
#include <algorithm>
#include <cmath>
#include <memory>
#include <utility>
#include <vector>
namespace ovv { namespace {
class Link2 final : public IDeviceAdapter {
 public:
  explicit Link2(std::string name):wanted_(std::move(name)){}
  ActionResult Connect() override {std::vector<uvc::UVCCameraInfo> ds;uvc::GetUVCCameraList(ds);auto it=wanted_.empty()?ds.begin():std::find_if(ds.begin(),ds.end(),[&](const auto& d){return d.friendly_name.find(wanted_)!=std::string::npos;});if(it==ds.end())return {false,ErrorCode::device_not_found,"Link 2 not found",{}};base_=std::make_unique<uvc::UVCCameraController>(*it);ext_=std::make_unique<uvc::UVCCameraExtendController>(*it);std::string sn;ext_->GetSerialNumber(sn);info_={"link2-"+(sn.empty()?std::to_string(it->video_device_index):sn),DeviceKind::link2,it->friendly_name,sn,{}, {ActionType::set_tracking,ActionType::set_composition,ActionType::set_track_speed,ActionType::set_ptz,ActionType::set_zoom,ActionType::set_privacy}};return {true,ErrorCode::ok,"Link 2 connected",{}};}
  void Disconnect() noexcept override{ext_.reset();base_.reset();} bool IsConnected()const noexcept override{return base_&&ext_;} DeviceInfo Info()const override{return info_;}
  bool Supports(ActionType a)const noexcept override{return std::find(info_.capabilities.begin(),info_.capabilities.end(),a)!=info_.capabilities.end();}
  ActionResult Execute(const DeviceAction&a)override{if(!IsConnected())return {false,ErrorCode::not_connected,"Link 2 not connected",{}};bool ok=false;switch(a.type){case ActionType::set_tracking:{uvc::VideoModeAuxiliaryData d{};ok=ext_->SetVideoMode(a.enabled?uvc::VideoMode::AutoComposition:uvc::VideoMode::Normal,d);break;}case ActionType::set_composition:{auto s=uvc::CompositionStyle::None;if(a.composition==Composition::head)s=uvc::CompositionStyle::OnlyHead;if(a.composition==Composition::half_body)s=uvc::CompositionStyle::HalfBody;if(a.composition==Composition::full_body)s=uvc::CompositionStyle::FullBody;ok=ext_->SetCompositionStyle(s);break;}case ActionType::set_track_speed:{auto s=uvc::TrackSpeed::Normal;if(a.track_speed==TrackSpeed::fast)s=uvc::TrackSpeed::Fast;if(a.track_speed==TrackSpeed::slow)s=uvc::TrackSpeed::Slow;ok=ext_->SetTrackSpeed(s);break;}case ActionType::set_ptz:ok=ext_->SetPanTiltAbsolute((int32_t)std::lround(a.pan_degrees*3600.0),(int32_t)std::lround(a.tilt_degrees*3600.0));break;case ActionType::set_zoom:ok=base_->SetZoomAbsolute((long)std::lround(a.zoom));break;case ActionType::set_privacy:ok=ext_->SetPrivacyMode(a.enabled);break;default:return {false,ErrorCode::unsupported,"unsupported Link 2 action",{}};}return ok?ActionResult{true,ErrorCode::ok,"Link 2 action executed",{}}:ActionResult{false,ErrorCode::vendor_error,"Link 2 SDK rejected action",{}};}
 private:std::string wanted_;DeviceInfo info_{"link2-pending",DeviceKind::link2,"Insta360 Link 2",{},{},{}};std::unique_ptr<uvc::UVCCameraController>base_;std::unique_ptr<uvc::UVCCameraExtendController>ext_;
}; }
std::shared_ptr<IDeviceAdapter> MakeLink2CameraAdapter(std::string name){return std::make_shared<Link2>(std::move(name));}
}
