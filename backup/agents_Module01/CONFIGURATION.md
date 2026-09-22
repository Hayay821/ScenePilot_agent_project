# 配置指南

## 环境变量配置

### .env 文件

在 `agents_Module/` 目录下创建 `.env` 文件：

```bash
# 百炼 API 配置（用于真实模型调用）
DASHSCOPE_API_KEY=your_dashscope_api_key_here
DASHSCOPE_MODEL_NAME=qwen-max

# 技能仓库路径（相对或绝对路径）
SKILL_REPOSITORY_PATH=./skills/repository

# 审计日志路径
AUDIT_LOG_PATH=./logs/audit.jsonl

# 用户级别默认值
DEFAULT_USER_LEVEL=beginner

# 日志级别
LOG_LEVEL=INFO
```

### 获取百炼 API Key

1. 访问 [阿里云百炼平台](https://dashscope.aliyun.com/)
2. 注册/登录账号
3. 进入控制台 → API-KEY 管理
4. 创建新的 API Key
5. 复制 API Key 到 `.env` 文件

### 可用模型

百炼平台支持的模型：

- `qwen-max` - 最强大的模型，适合复杂推理
- `qwen-plus` - 平衡性能和成本
- `qwen-turbo` - 快速响应，适合简单任务

## Python 依赖安装

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或手动安装核心依赖
pip install pydantic>=2.0.0
pip install pyyaml>=6.0.1
pip install pytest>=7.4.0
pip install python-dotenv>=1.0.0
```

## 目录结构要求

确保以下目录存在：

```bash
mkdir -p logs
mkdir -p skills/repository/builtin/director
mkdir -p skills/repository/builtin/cinematographer
mkdir -p skills/repository/builtin/editor
mkdir -p skills/repository/community
mkdir -p skills/repository/personal
mkdir -p skills/repository/pending_review
```

## 技能配置

### 技能存储位置

技能按以下结构组织：

```
skills/repository/
├── builtin/          # 内置系统技能（只读）
│   ├── director/
│   ├── cinematographer/
│   └── editor/
├── community/        # 社区共享技能
├── personal/         # 个人自定义技能
└── pending_review/   # 待审核技能
```

### 加载优先级

系统按以下顺序搜索技能：

1. `builtin/` - 内置技能（最高优先级）
2. `community/` - 社区技能
3. `personal/` - 个人技能
4. `pending_review/` - 待审核技能

同名技能取第一个找到的版本。

## 设备配置

### 支持的设备

在代码中指定可用设备：

```python
available_devices = [
    "insta360_link2",    # Link 2 摄像头
    "insta360_x4_air",   # X4 Air 全景相机
]
```

### 设备能力映射

不同设备支持不同功能：

**Link 2**:
- 人脸跟踪
- 云台控制
- 高清录制
- 适合：近景、半身、人像特写

**X4 Air**:
- 360° 全景
- 空间音频
- 环境记录
- 适合：环境、群组、全景重构

## 用户级别配置

系统支持三种用户级别：

### beginner（初学者）

```python
user_level = "beginner"
```

特性：
- 提供详细的摄影原理解释
- 显示决策依据
- 避免专业术语
- 保守的拍摄建议

### intermediate（中级用户）

```python
user_level = "intermediate"
```

特性：
- 简化的解释
- 平衡安全和创意
- 假设基础摄影知识
- 提供更多选项

### expert（专家）

```python
user_level = "expert"
```

特性：
- 最少的解释
- 允许创建和修改技能
- 可发布技能到社区
- 直接访问高级功能

## 输出配置

### 视频格式

```python
output_requirements = {
    "aspect_ratio": "9:16",      # 竖屏 (或 "16:9", "1:1")
    "duration_target_ms": 10000,  # 目标时长 10 秒
    "resolution": "1080p",        # 分辨率
    "fps": 30,                    # 帧率
    "format": "mp4"               # 输出格式
}
```

### 常用比例

- `16:9` - 横屏视频（YouTube、电视）
- `9:16` - 竖屏视频（TikTok、Instagram Stories）
- `1:1` - 方形（Instagram Feed）
- `4:5` - 竖版（Instagram Feed）

## 日志配置

### 审计日志格式

审计日志使用 JSONL 格式（每行一个 JSON 对象）：

```jsonl
{"session_id": "uuid", "timestamp": "2026-09-22T10:30:00Z", "step": "intent", "result": {...}}
```

### 日志级别

在代码中设置：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

级别：
- `DEBUG` - 详细调试信息
- `INFO` - 一般信息（推荐）
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误

## 性能配置

### Mock Provider（测试用）

用于快速测试，不调用真实 API：

```python
from agents_Module.providers import MockProvider

provider = MockProvider()
```

### 真实 Provider（生产用）

连接百炼 API：

```python
from agents_Module.providers.dashscope_provider import DashScopeProvider
import os
from dotenv import load_dotenv

load_dotenv()

provider = DashScopeProvider(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model_name=os.getenv("DASHSCOPE_MODEL_NAME", "qwen-max")
)
```

### 超时配置

```python
provider = DashScopeProvider(
    api_key="...",
    model_name="qwen-max",
    timeout=30,           # API 超时（秒）
    max_retries=3,        # 最大重试次数
    retry_delay=1.0       # 重试延迟（秒）
)
```

## 安全配置

### 动作白名单

在技能 YAML 中配置：

```yaml
safety:
  allowed_actions:
    - suggest_composition
    - suggest_tracking
    - suggest_reframe
  
  forbidden_actions:
    - delete_media
    - format_storage
    - direct_device_control
  
  min_confidence_for_tracking_suggestion: 0.70
  
  requires_human_approval:
    - change_primary_subject
    - exposure_override
```

### 置信度阈值

```python
# 在 SkillValidator 中配置
validator = SkillValidator()

# 默认阈值
DEFAULT_MIN_CONFIDENCE = 0.50          # 一般建议
TRACKING_MIN_CONFIDENCE = 0.70         # 跟踪建议
DEVICE_CHANGE_MIN_CONFIDENCE = 0.70    # 设备切换
SCENE_CHANGE_MIN_CONFIDENCE = 0.60     # 场景变更
```

## 测试配置

### Pytest 配置

创建 `pytest.ini`：

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    integration: 集成测试
    unit: 单元测试
    slow: 慢速测试
```

### 运行特定测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢速测试
pytest -m "not slow"

# 详细输出
pytest -vv

# 显示打印输出
pytest -s
```

## 开发配置

### IDE 配置（VS Code）

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

### Git 配置

确保 `.gitignore` 包含：

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# 环境变量
.env
.env.local

# 日志
logs/
*.log

# IDE
.vscode/
.idea/
*.swp

# 测试
.pytest_cache/
.coverage
htmlcov/

# 个人技能（可选）
skills/repository/personal/
```

## 故障排除

### 技能加载失败

检查文件路径和权限：

```bash
# 检查文件是否存在
ls -la skills/repository/builtin/director/

# 检查文件权限
chmod 644 skills/repository/builtin/director/*.yaml
```

### API 调用失败

检查 API Key 和网络：

```python
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    print("❌ DASHSCOPE_API_KEY not found in .env")
else:
    print(f"✓ API Key loaded: {api_key[:10]}...")
```

### 依赖版本冲突

更新到最新兼容版本：

```bash
# 升级特定包
pip install --upgrade pydantic

# 或重新安装所有依赖
pip install -r requirements.txt --upgrade
```

## 生产部署配置

### 环境变量管理

生产环境使用系统环境变量，不使用 `.env` 文件：

```bash
# Linux/macOS
export DASHSCOPE_API_KEY="your_key"
export DASHSCOPE_MODEL_NAME="qwen-max"
export LOG_LEVEL="WARNING"

# Windows
set DASHSCOPE_API_KEY=your_key
set DASHSCOPE_MODEL_NAME=qwen-max
set LOG_LEVEL=WARNING
```

### 日志轮转

使用 `logging.handlers.RotatingFileHandler`：

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO
)
```

### 性能监控

```python
import time

def log_performance(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logging.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

---

**配置完成后，运行测试验证：**

```bash
python -m agents_Module list
python examples/complete_workflow.py
pytest tests/ -v
```
