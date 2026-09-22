#include "ovv/media_processor.h"
#include <stitcher/ins_stitcher.h>
#include <algorithm>
#include <cctype>
#include <memory>
#include <mutex>
#include <unordered_map>
#include <utility>
namespace ovv { namespace {
ins::STITCH_TYPE VendorType(StitchAlgorithm a){switch(a){case StitchAlgorithm::template_stitch:return ins::STITCH_TYPE::TEMPLATE;case StitchAlgorithm::dynamic_stitch:return ins::STITCH_TYPE::DYNAMICSTITCH;case StitchAlgorithm::ai_stitch:return ins::STITCH_TYPE::AIFLOW;default:return ins::STITCH_TYPE::OPTFLOW;}}
bool IsImage(std::string p){std::transform(p.begin(),p.end(),p.begin(),[](unsigned char c){return(char)std::tolower(c);});return(p.size()>=5&&p.rfind(".insp")==p.size()-5)||(p.size()>=4&&p.rfind(".jpg")==p.size()-4);}
class Media final:public IMediaProcessor{
 public:explicit Media(const std::string&models){ins::InitEnv();ins::SetModelFileRootDir(models);}
 MediaJob Submit(const StitchRequest&r)override{if(r.request_id.empty()||r.inputs.empty()||r.output.empty())return{r.request_id,MediaJobState::failed,0,r.output,"request_id, inputs and output required"};if(IsImage(r.inputs.front())){ins::ImageStitcher s;s.SetInputPath(r.inputs);s.SetOutputPath(r.output);s.SetOutputSize(r.output_width,r.output_height);s.SetStitchType(VendorType(r.algorithm));s.EnableFlowState(r.flow_state);s.EnableStitchFusion(r.stitch_fusion);bool ok=s.Stitch();MediaJob j{r.request_id,ok?MediaJobState::succeeded:MediaJobState::failed,ok?100:0,r.output,ok?"":"image stitch failed"};std::lock_guard<std::mutex>l(m_);jobs_[j.id]=j;return j;}auto s=std::make_shared<ins::VideoStitcher>();s->SetInputPath(r.inputs);s->SetOutputPath(r.output);s->SetOutputSize(r.output_width,r.output_height);s->SetStitchType(VendorType(r.algorithm));s->EnableFlowState(r.flow_state);s->EnableDirectionLock(r.direction_lock);s->EnableStitchFusion(r.stitch_fusion);{std::lock_guard<std::mutex>l(m_);jobs_[r.request_id]={r.request_id,MediaJobState::running,0,r.output,{}};active_[r.request_id]=s;}s->SetStitchProgressCallback([this,id=r.request_id](int p,int e){std::lock_guard<std::mutex>l(m_);auto&j=jobs_[id];j.progress=p;if(e){j.state=MediaJobState::failed;j.error="MediaSDK error "+std::to_string(e);active_.erase(id);}else if(p>=100){j.state=MediaJobState::succeeded;active_.erase(id);}});s->SetStitchStateCallback([this,id=r.request_id](int e,const char*msg){if(!e)return;std::lock_guard<std::mutex>l(m_);auto&j=jobs_[id];j.state=MediaJobState::failed;j.error=msg?msg:"MediaSDK state error";active_.erase(id);});s->StartStitch();return Get(r.request_id);}
 MediaJob Get(const std::string&id)const override{std::lock_guard<std::mutex>l(m_);auto it=jobs_.find(id);return it==jobs_.end()?MediaJob{id,MediaJobState::failed,0,{},"job not found"}:it->second;}
 bool Cancel(const std::string&id)override{std::shared_ptr<ins::VideoStitcher>s;{std::lock_guard<std::mutex>l(m_);auto it=active_.find(id);if(it==active_.end())return false;s=it->second;}bool ok=s->CancelStitch();if(ok){std::lock_guard<std::mutex>l(m_);jobs_[id].state=MediaJobState::cancelled;active_.erase(id);}return ok;}
 private:mutable std::mutex m_;std::unordered_map<std::string,MediaJob>jobs_;std::unordered_map<std::string,std::shared_ptr<ins::VideoStitcher>>active_;
}; }
std::shared_ptr<IMediaProcessor> MakeInsta360MediaProcessor(std::string models){return std::make_shared<Media>(std::move(models));}
}
