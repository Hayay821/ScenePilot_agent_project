#include "ovv/media_processor.h"

#include <mutex>
#include <unordered_map>

namespace ovv {
namespace {

class MockMediaProcessor final : public IMediaProcessor {
public:
    MediaJob Submit(const StitchRequest& request) override {
        MediaJob job;
        job.id = request.request_id.empty() ? "mock-media-job" : request.request_id;
        job.output = request.output;
        if (request.inputs.empty() || request.output.empty()) {
            job.state = MediaJobState::failed;
            job.error = "必须提供输入和输出路径";
        } else {
            job.state = MediaJobState::succeeded;
            job.progress = 100;
        }
        std::lock_guard<std::mutex> lock(mutex_);
        jobs_[job.id] = job;
        return job;
    }
    MediaJob Get(const std::string& job_id) const override {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto it = jobs_.find(job_id);
        return it == jobs_.end() ? MediaJob{job_id, MediaJobState::failed, 0, {}, "未找到任务"} : it->second;
    }
    bool Cancel(const std::string& job_id) override {
        std::lock_guard<std::mutex> lock(mutex_);
        const auto it = jobs_.find(job_id);
        if (it == jobs_.end() || it->second.state == MediaJobState::succeeded) return false;
        it->second.state = MediaJobState::cancelled;
        return true;
    }
private:
    mutable std::mutex mutex_;
    mutable std::unordered_map<std::string, MediaJob> jobs_;
};

}  // namespace

std::shared_ptr<IMediaProcessor> MakeMockMediaProcessor() {
    return std::make_shared<MockMediaProcessor>();
}

}  // namespace ovv


