"""
配置管理 - 使用 Pydantic Settings 从环境变量加载配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """全局配置"""

    # 百炼 API 配置
    dashscope_api_key: str = "mock-key"
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    qwen_vl_model: str = "qwen-vl-max"
    qwen_text_model: str = "qwen-plus"
    cache_dir: Path = Path("cache")
    # STC 压缩参数
    stc_frame_diff_threshold: float = 0.15
    stc_hist_diff_threshold: float = 0.20
    stc_phash_threshold: int = 5
    stc_max_gap_sec: int = 3
    stc_min_frames_per_window: int = 1
    stc_max_frames_per_window: int = 4
    stc_window_size_sec: int = 4

    # 视频输入配置
    video_sample_fps: int = 2
    video_max_dimension: int = 384
    ring_buffer_duration_sec: int = 10

    # 语义模型配置
    semantic_batch_size: int = 3
    semantic_timeout_sec: int = 30
    semantic_max_retries: int = 2
    semantic_cache_enabled: bool = True

    # 导演状态机配置
    director_idle_timeout_ms: int = 10000       # 10 秒空闲超时
    director_search_timeout_ms: int = 10000     # 10 秒搜索超时
    director_recover_timeout_ms: int = 5000     # 5 秒恢复超时

    # 高光剪辑配置
    highlight_preroll_ms: int = 3000
    highlight_postroll_ms: int = 3000
    highlight_min_duration_ms: int = 2000

    # 日志级别
    log_level: str = "INFO"

    # 项目路径
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    keyframes_dir: Path = data_dir / "keyframes"
    output_dir: Path = data_dir / "output"
    input_dir: Path = data_dir / "input"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator('dashscope_api_key', mode='before')
    @classmethod
    def strip_api_key(cls, v):
        """去除 API Key 首尾空格"""
        if isinstance(v, str):
            return v.strip()
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保必要的目录存在
        self.ensure_directories()

    def ensure_directories(self):
        """创建必要的目录"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.keyframes_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)

    @property
    def is_mock_mode(self) -> bool:
        """判断是否为 Mock 模式（没有真实 API Key）"""
        return self.dashscope_api_key == "mock-key" or not self.dashscope_api_key.startswith("sk-")


# 全局配置实例
settings = Settings()
