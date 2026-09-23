#include "ovv/device_adapter.h"
#include <camera/camera.h>
#include <camera/device_discovery.h>
#include <stream/stream_delegate.h>
#include <ins_realtime_stitcher.h>
#include <windows.h>
#include <algorithm>
#include <cstring>
#include <cstdlib>
#include <filesystem>
#include <memory>
#include <mutex>
#include <utility>
#include <vector>

namespace ovv { namespace {

constexpr int kStitchWidth = 960;
constexpr int kStitchHeight = 480;

class FfmpegPipe {
public:
    bool Start() {
        SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
        HANDLE read_pipe = nullptr;
        if (!CreatePipe(&read_pipe, &write_pipe_, &sa, 0)) return false;
        SetHandleInformation(write_pipe_, HANDLE_FLAG_INHERIT, 0);
        CreateDirectoryW(L"preview", nullptr);
        HANDLE null_handle = CreateFileW(L"NUL", GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                         &sa, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
        STARTUPINFOW si{}; si.cb = sizeof(si); si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = read_pipe; si.hStdOutput = null_handle; si.hStdError = null_handle;
        std::wstring command =
            L"\".\\ffmpeg\\bin\\ffmpeg.exe\" -hide_banner -loglevel error "
            L"-f rawvideo -pixel_format rgba -video_size 960x480 -framerate 30 -i pipe:0 "
            L"-vf fps=10 -q:v 4 -update 1 -y preview\\x5_latest.jpg";
        std::vector<wchar_t> args(command.begin(), command.end()); args.push_back(L'\0');
        PROCESS_INFORMATION pi{};
        const BOOL ok = CreateProcessW(nullptr, args.data(), nullptr, nullptr, TRUE, CREATE_NO_WINDOW,
                                       nullptr, nullptr, &si, &pi);
        CloseHandle(read_pipe); CloseHandle(null_handle);
        if (!ok) { Close(); return false; }
        process_ = pi.hProcess; CloseHandle(pi.hThread); return true;
    }
    bool WriteFrame(const uint8_t* data, int stride, int width, int height) {
        if (!data || width != kStitchWidth || height != kStitchHeight) return false;
        std::lock_guard<std::mutex> lock(mutex_);
        if (!write_pipe_) return false;
        const DWORD row_bytes = static_cast<DWORD>(width * 4);
        for (int y = 0; y < height; ++y) {
            const uint8_t* row = data + static_cast<size_t>(y) * stride;
            DWORD offset = 0;
            while (offset < row_bytes) {
                DWORD written = 0;
                if (!WriteFile(write_pipe_, row + offset, row_bytes - offset, &written, nullptr) || written == 0)
                    return false;
                offset += written;
            }
        }
        return true;
    }
    void Close() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (write_pipe_) { CloseHandle(write_pipe_); write_pipe_ = nullptr; }
        if (process_) {
            if (WaitForSingleObject(process_, 1500) == WAIT_TIMEOUT) TerminateProcess(process_, 0);
            CloseHandle(process_); process_ = nullptr;
        }
    }
    ~FfmpegPipe() { Close(); }
private:
    HANDLE write_pipe_{nullptr};
    HANDLE process_{nullptr};
    std::mutex mutex_;
};

class StitchDelegate final : public ins_camera::StreamDelegate {
public:
    explicit StitchDelegate(std::shared_ptr<ins::RealTimeStitcher> stitcher) : stitcher_(std::move(stitcher)) {}
    void OnVideoData(const uint8_t* data, size_t size, int64_t timestamp, uint8_t stream_type, int stream_index) override {
        stitcher_->HandleVideoData(data, size, timestamp, stream_type, stream_index);
    }
    void OnAudioData(const uint8_t*, size_t, int64_t) override {}
    void OnGyroData(const std::vector<ins_camera::GyroData>& data) override {
        std::vector<ins::GyroData> converted(data.size());
        if (!data.empty()) std::memcpy(converted.data(), data.data(), data.size() * sizeof(ins_camera::GyroData));
        stitcher_->HandleGyroData(converted);
    }
    void OnExposureData(const ins_camera::ExposureData& data) override {
        ins::ExposureData converted{};
        converted.exposure_time = data.exposure_time;
        converted.timestamp = data.timestamp;
        stitcher_->HandleExposureData(converted);
    }
private:
    std::shared_ptr<ins::RealTimeStitcher> stitcher_;
};

class X5 final : public IDeviceAdapter {
public:
    explicit X5(std::string serial): wanted_(std::move(serial)) {}
    ActionResult Connect() override {
        static std::once_flag media_init;
        std::call_once(media_init, [] { ins::InitEnv(); ins::SetLogLevel(ins::InsLogLevel::WARNING); });
        ins_camera::DeviceDiscovery discovery; auto devices=discovery.GetAvailableDevices();
        auto it=wanted_.empty()?devices.begin():std::find_if(devices.begin(),devices.end(),
            [&](const auto& d){return d.serial_number==wanted_;});
        if(it==devices.end()){discovery.FreeDeviceDescriptors(devices);return {false,ErrorCode::device_not_found,"未发现X5设备",{}};}
        info_={"x5-"+it->serial_number,DeviceKind::x5,it->camera_name,it->serial_number,it->fw_version,
            {ActionType::capture_photo,ActionType::start_recording,ActionType::stop_recording,
             ActionType::start_preview,ActionType::stop_preview,ActionType::download_media,ActionType::shutdown}};
        camera_=std::make_shared<ins_camera::Camera>(it->info); bool ok=camera_->Open();
        discovery.FreeDeviceDescriptors(devices);
        if(!ok){camera_.reset();return {false,ErrorCode::vendor_error,"Camera::Open 调用失败",{}};}
        return {true,ErrorCode::ok,"X5连接成功",{}};
    }
    void Disconnect() noexcept override {
        if(camera_ && stitcher_) camera_->StopLiveStreaming();
        StopPreviewResources();
        if(camera_)camera_->Close();camera_.reset();
    }
    bool IsConnected() const noexcept override {return camera_&&camera_->IsConnected();}
    DeviceInfo Info() const override{return info_;}
    bool Supports(ActionType a) const noexcept override{return std::find(info_.capabilities.begin(),info_.capabilities.end(),a)!=info_.capabilities.end();}
    ActionResult Execute(const DeviceAction& a) override {
        if(!camera_)return {false,ErrorCode::not_connected,"X5尚未连接",{}};
        switch(a.type){
        case ActionType::capture_photo:{if(stitcher_){camera_->StopLiveStreaming();stitcher_->CancelStitch();StopPreviewResources();}if(!camera_->SetPhotoSubMode(ins_camera::SubPhotoMode::PHOTO_SINGLE))return {false,ErrorCode::vendor_error,"切换普通拍照模式失败",{}};auto m=camera_->TakePhoto();if(m.Empty())return {false,ErrorCode::vendor_error,"TakePhoto 调用失败",{}};return DownloadCapturedMedia(m,"照片");}
        case ActionType::start_recording:{if(stitcher_){camera_->StopLiveStreaming();stitcher_->CancelStitch();StopPreviewResources();}if(!camera_->SetVideoSubMode(ins_camera::SubVideoMode::VIDEO_NORMAL))return {false,ErrorCode::vendor_error,"切换普通录像模式失败",{}};bool ok=camera_->StartRecording();return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,ok?"录像已开始":"开始录像失败",{}};}
        case ActionType::stop_recording:{auto m=camera_->StopRecording();if(m.Empty())return {false,ErrorCode::vendor_error,"StopRecording 调用失败",{}};return DownloadCapturedMedia(m,"视频");}
        case ActionType::start_preview:return StartStitchedPreview();
        case ActionType::stop_preview:{
            bool ok=camera_->StopLiveStreaming();
            if(stitcher_)stitcher_->CancelStitch();
            StopPreviewResources();
            return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,ok?"X5全景实时预览已停止":"停止实时预览失败",{}};
        }
        case ActionType::download_media:{bool ok=camera_->DownloadCameraFile(a.source_path,a.destination_path);return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,ok?"素材下载成功":"素材下载失败",a.destination_path};}
        case ActionType::shutdown:{bool ok=camera_->ShutdownCamera();return {ok,ok?ErrorCode::ok:ErrorCode::vendor_error,ok?"相机已关闭":"关闭相机失败",{}};}
        default:return {false,ErrorCode::unsupported,"X5不支持该动作",{}};
        }
    }
private:
    ActionResult DownloadCapturedMedia(const ins_camera::MediaUrl& media, const std::string& label) {
        const char* configured = std::getenv("OVV_ASSET_DIR");
        if (!configured || !*configured) return {true, ErrorCode::ok, label + "已保存在相机中", media.GetSingleOrigin()};
        std::filesystem::path directory(configured);
        std::error_code error;
        std::filesystem::create_directories(directory, error);
        std::string first_web_path;
        for (const auto& remote : media.OriginUrls()) {
            auto slash = remote.find_last_of("/\\");
            auto name = slash == std::string::npos ? remote : remote.substr(slash + 1);
            if (name.empty()) continue;
            auto destination = directory / std::filesystem::u8path(name);
            if (!camera_->DownloadCameraFile(remote, destination.u8string()))
                return {false, ErrorCode::vendor_error, label + "拍摄成功，但下载到项目素材库失败", remote};
            if (first_web_path.empty()) first_web_path = "assets/captures/" + name;
        }
        return {true, ErrorCode::ok, label + "已保存到项目素材库", first_web_path};
    }

    ActionResult StartStitchedPreview() {
        if(stitcher_)return {true,ErrorCode::ok,"X5全景实时预览已在运行",{}};
        DeleteFileW(L"preview\\x5_latest.jpg");
        pipe_=std::make_shared<FfmpegPipe>();
        if(!pipe_->Start()){pipe_.reset();return {false,ErrorCode::vendor_error,"FFmpeg启动失败",{}};
        }
        stitcher_=std::make_shared<ins::RealTimeStitcher>();
        auto preview=camera_->GetPreviewParam();
        ins::CameraInfo camera_info;
        camera_info.cameraName=preview.camera_name;
        camera_info.decode_type=static_cast<ins::VideoDecodeType>(preview.encode_type);
        std::vector<std::string> calibration;
        for(size_t i=0;i<preview.GetCalibrationCount();++i)calibration.push_back(preview.GetCalibration(i));
        camera_info.SetCalibration(calibration,preview.GetCropSrcWidth(),preview.GetCropSrcHeight(),
            preview.GetCropDstWidth(),preview.GetCropDstHeight(),preview.GetCropOffsetX(),preview.GetCropOffsetY());
        stitcher_->SetCameraInfo(camera_info);
        stitcher_->SetStitchType(ins::STITCH_TYPE::DYNAMICSTITCH);
        stitcher_->EnableFlowState(true);
        stitcher_->SetOutputSize(kStitchWidth,kStitchHeight);
        std::weak_ptr<FfmpegPipe> weak_pipe=pipe_;
        stitcher_->SetStitchRealTimeDataCallback([weak_pipe](uint8_t* data[4],int linesize[4],int width,int height,int,int64_t){
            if(auto pipe=weak_pipe.lock())pipe->WriteFrame(data[0],linesize[0],width,height);
        });
        delegate_=std::make_shared<StitchDelegate>(stitcher_);
        camera_->SetStreamDelegate(delegate_);
        ins_camera::LiveStreamParam p;
        p.video_resolution=ins_camera::VideoResolution::RES_1440_720P30;
        p.lrv_video_resulution=p.video_resolution;p.video_bitrate=1024*1024/2;p.enable_audio=false;p.using_lrv=false;
        if(!camera_->StartLiveStreaming(p)){StopPreviewResources();return {false,ErrorCode::vendor_error,"CameraSDK启动预览失败",{}};
        }
        stitcher_->StartStitch();
        return {true,ErrorCode::ok,"X5全景实时预览已开始",{}};
    }
    void StopPreviewResources(){
        delegate_.reset();
        if(stitcher_){stitcher_->CancelStitch();stitcher_.reset();}
        if(pipe_){pipe_->Close();pipe_.reset();}
    }
    std::string wanted_;DeviceInfo info_{"x5-pending",DeviceKind::x5,"Insta360 X5",{},{},{}};
    std::shared_ptr<ins_camera::Camera> camera_;
    std::shared_ptr<FfmpegPipe> pipe_;
    std::shared_ptr<ins::RealTimeStitcher> stitcher_;
    std::shared_ptr<ins_camera::StreamDelegate> delegate_;
};
}
std::shared_ptr<IDeviceAdapter> MakeX5CameraAdapter(std::string serial){return std::make_shared<X5>(std::move(serial));}
}