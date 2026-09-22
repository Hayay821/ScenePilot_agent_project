#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace ovv {

enum class StitchAlgorithm { template_stitch, optical_flow, dynamic_stitch, ai_stitch };
enum class MediaJobState { pending, running, succeeded, failed, cancelled };

struct StitchRequest {
    std::string request_id;
    std::vector<std::string> inputs;
    std::string output;
    StitchAlgorithm algorithm{StitchAlgorithm::optical_flow};
    int output_width{3840};
    int output_height{1920};
    bool flow_state{true};
    bool direction_lock{false};
    bool stitch_fusion{false};
    bool color_plus{false};
};

struct MediaJob {
    std::string id;
    MediaJobState state{MediaJobState::pending};
    int progress{0};
    std::string output;
    std::string error;
};

class IMediaProcessor {
public:
    virtual ~IMediaProcessor() = default;
    virtual MediaJob Submit(const StitchRequest& request) = 0;
    virtual MediaJob Get(const std::string& job_id) const = 0;
    virtual bool Cancel(const std::string& job_id) = 0;
};

std::shared_ptr<IMediaProcessor> MakeMockMediaProcessor();

#ifdef OVV_ENABLE_MEDIA_SDK
std::shared_ptr<IMediaProcessor> MakeInsta360MediaProcessor(std::string model_root);
#endif

}  // namespace ovv


