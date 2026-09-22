# API 集成指南

本指南说明如何将 agents_Module 与真实的 AI API（如阿里云百炼 DashScope）集成。

## 支持的 API 提供商

### 1. DashScope (阿里云百炼) - 推荐

阿里云的通义千问大模型服务，支持 qwen-max、qwen-plus、qwen-turbo 等模型。

**优势**:
- 中文理解能力强
- 响应速度快
- 价格合理
- 支持结构化输出

### 2. MockProvider (测试用)

用于开发和测试的模拟提供商，返回确定性的测试数据。

## 快速开始：DashScope API

### 步骤 1: 安装依赖

```bash
pip install dashscope
```

### 步骤 2: 获取 API Key

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 创建应用并获取 API Key
3. 设置环境变量

**Windows CMD**:
```cmd
set DASHSCOPE_API_KEY=sk-your-api-key-here
```

**Windows PowerShell**:
```powershell
$env:DASHSCOPE_API_KEY="sk-your-api-key-here"
```

**Linux/Mac**:
```bash
export DASHSCOPE_API_KEY="sk-your-api-key-here"
```

**或者在 Python 中设置**:
```python
import os
os.environ["DASHSCOPE_API_KEY"] = "sk-your-api-key-here"
```

### 步骤 3: 使用 DashScopeProvider

```python
from agents_Module.providers import DashScopeProvider
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.skills import SkillRepository, SkillValidator

# 初始化 provider
provider = DashScopeProvider(
    api_key="sk-your-api-key-here",  # 或从环境变量读取
    model_name="qwen-max",           # qwen-max, qwen-plus, qwen-turbo
    timeout=30,
    max_retries=3
)

# 初始化 orchestrator
repo = SkillRepository("./skills/repository")
validator = SkillValidator()

orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=provider  # 使用真实 API
)

# 运行工作流
result = orchestrator.run_complete_workflow(
    user_input="拍摄自然个人肖像用作社交媒体头像",
    devices=["osmo_pocket_3"],
    user_level="intermediate"
)

print(f"Creative Goal: {result['director_plan']['creative_goal']}")
```

### 步骤 4: 运行示例

```bash
# 设置 API key
export DASHSCOPE_API_KEY="sk-your-api-key-here"

# 运行示例
python examples/dashscope_demo.py
```

## 模型选择

### qwen-max (推荐)
- **最强能力**: 理解力和创造力最好
- **适合**: 复杂场景规划、创意建议
- **速度**: 较慢
- **价格**: 最高

### qwen-plus
- **平衡选择**: 能力和速度平衡
- **适合**: 大部分场景
- **速度**: 适中
- **价格**: 适中

### qwen-turbo
- **快速响应**: 响应最快
- **适合**: 实时建议、简单任务
- **速度**: 最快
- **价格**: 最低

## 高级配置

### 自定义参数

```python
provider = DashScopeProvider(
    api_key=api_key,
    model_name="qwen-max",
    timeout=60,        # 超时时间（秒）
    max_retries=5      # 最大重试次数
)

# 调用时设置温度和 top_p
result = provider.call(
    prompt="拍摄计划",
    schema=DirectorPlan,
    temperature=0.7,   # 0.0 - 2.0，越高越有创造性
    top_p=0.9          # 0.0 - 1.0，核采样参数
)
```

### 错误处理

```python
try:
    result = orchestrator.run_complete_workflow(
        user_input=user_input,
        devices=devices,
        user_level=user_level
    )
except RuntimeError as e:
    print(f"API 调用失败: {e}")
except ValueError as e:
    print(f"响应解析失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

### 使用回退机制

DashScopeProvider 内置了自动重试和指数退避机制：

```python
# 自动重试，失败时指数退避
result = provider.call_with_retry(
    prompt="拍摄计划",
    schema=DirectorPlan,
    temperature=0.7
)
```

## 成本控制

### 估算 API 调用次数

一个完整工作流通常包括：

1. **Pre-production (预制作)**: 4 次 API 调用
   - normalize_intent (意图归一化)
   - retrieve_skills (技能检索)
   - create_bundle (创建技能包)
   - create_plan (创建导演计划)

2. **Filming (拍摄中)**: N 次 API 调用
   - 每个拍摄步骤 1 次 (make_recommendation)

3. **Post-production (后期)**: 1 次 API 调用
   - create_timeline (创建剪辑时间线)

**总计**: 5 + N 次 API 调用（N = 拍摄步骤数）

### 优化策略

1. **使用 Mock 模式进行开发和测试**
```python
from agents_Module.providers import MockProvider
orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=MockProvider()  # 开发时使用 Mock
)
```

2. **缓存 Pre-production 结果**
```python
# 保存 session_id 和 plan
session_id = result["session_id"]
plan = result["director_plan"]

# 后续拍摄步骤复用 session
orchestrator.run_filming_step(
    session_id=session_id,
    current_stage="main_action",
    subject_state=subject_state,
    recent_events=events
)
```

3. **批量处理**
```python
# 一次处理多个事件
events = [
    {"timestamp": 1000, "type": "subject_detected"},
    {"timestamp": 2000, "type": "motion_detected"},
    {"timestamp": 3000, "type": "highlight_moment"}
]

# Editor 一次处理所有事件
edit_result = orchestrator.run_post_production(
    session_id=session_id,
    captured_events=events
)
```

## 环境变量配置文件

创建 `.env` 文件（不要提交到 Git）：

```bash
# .env
DASHSCOPE_API_KEY=sk-your-api-key-here
DASHSCOPE_MODEL=qwen-max
DASHSCOPE_TIMEOUT=30
DASHSCOPE_MAX_RETRIES=3
```

在代码中加载：

```python
from dotenv import load_dotenv
load_dotenv()

provider = DashScopeProvider(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    model_name=os.getenv("DASHSCOPE_MODEL", "qwen-max"),
    timeout=int(os.getenv("DASHSCOPE_TIMEOUT", "30")),
    max_retries=int(os.getenv("DASHSCOPE_MAX_RETRIES", "3"))
)
```

## 开发建议

### 1. 先用 Mock 开发

```python
# 开发阶段
orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=MockProvider()
)

# 测试通过后切换到真实 API
orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=DashScopeProvider()
)
```

### 2. 记录 API 调用日志

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashscope")

# 在 provider 中记录调用
logger.info(f"API call: {model_name}, tokens: {usage}")
```

### 3. 实现 Provider 抽象

所有 provider 应该实现相同的接口：

```python
class BaseProvider:
    def call(self, prompt: str, schema: Type[BaseModel], **kwargs) -> Dict[str, Any]:
        """Call API with structured output"""
        raise NotImplementedError

    def call_with_retry(self, prompt: str, schema: Type[BaseModel], **kwargs) -> Dict[str, Any]:
        """Call with retry logic"""
        raise NotImplementedError
```

## 故障排查

### 问题 1: ModuleNotFoundError: No module named 'dashscope'

**解决**: 安装 dashscope 包
```bash
pip install dashscope
```

### 问题 2: DashScope API error: 401 - Unauthorized

**原因**: API key 无效或未设置

**解决**: 检查 API key 是否正确设置
```python
import os
print(os.getenv("DASHSCOPE_API_KEY"))
```

### 问题 3: Failed to parse JSON response

**原因**: 模型返回的不是有效 JSON

**解决**: 
1. 检查 prompt 是否清晰
2. 尝试降低 temperature 参数
3. 使用更强的模型 (qwen-max)

### 问题 4: Request timeout

**原因**: API 响应超时

**解决**:
```python
provider = DashScopeProvider(
    timeout=60,  # 增加超时时间
    max_retries=5  # 增加重试次数
)
```

## 更多资源

- [DashScope API 文档](https://help.aliyun.com/zh/dashscope/)
- [通义千问模型介绍](https://help.aliyun.com/zh/dashscope/developer-reference/model-introduction)
- [API 定价](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-metering-and-billing)

## 下一步

1. **测试 Mock 模式**: `python examples/complete_workflow.py`
2. **配置 API Key**: 设置环境变量
3. **运行真实 API**: `python examples/dashscope_demo.py`
4. **集成到应用**: 参考 [IMPLEMENTATION.md](IMPLEMENTATION.md)
