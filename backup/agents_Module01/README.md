# ScenePilot Agent Module

**智能摄影助手的多 Agent 协作系统**

## 概述

agents_Module 是 ScenePilot 项目的核心智能层，通过四个专业化 Agent 协作完成从用户意图到最终成片的完整工作流：

- **SkillsManager**: 意图归一化、技能检索和技能组合
- **Director**: 创意规划、分阶段镜头意图和拍摄优先级
- **Cinematographer**: 实时拍摄建议（构图、景别、跟踪）
- **Editor**: 事件驱动时间线创建和成片规划

### 核心特性

✅ **技能驱动架构** - 所有拍摄逻辑通过 YAML 技能描述，支持版本管理、搜索和扩展  
✅ **安全优先** - 白名单动作控制，Agent 只提供建议不直接控制设备  
✅ **教学模式** - 为初学者提供摄影原理解释和决策依据  
✅ **完整测试覆盖** - 单元测试、集成测试和端到端测试  
✅ **Mock Provider** - 无需 API 调用即可测试完整工作流  

---

## 架构设计

### 核心层次

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentOrchestrator                        │
│               (工作流编排与会话管理)                           │
│    - 注入 Provider 到各 Agent                                 │
│    - 使用 Schema 验证所有数据流                               │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ SkillsManager│   │   Director   │   │Cinematographer│
│   Agent      │   │    Agent     │   │    Agent      │
└──────────────┘   └──────────────┘   └──────────────┘
    │                   │                   │
    │ 使用 Provider     │ 生成 Schema      │ 返回 Schema
    │ 返回 Schema       │ 输出             │ 对象
    │                   │                   │
    └───────────────────┼───────────────────┘
                        ▼
            ┌──────────────────────┐
            │    Editor Agent      │
            │  (接收 Schema 输入)   │
            └──────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│Skill Repository│   │  Schemas     │   │  Providers   │
│  (YAML Skills) │   │ (Pydantic)   │   │(Mock/Bailian)│
│                │   │              │   │              │
│ 被 Validator   │   │ 定义所有数据 │   │ LLM 抽象层   │
│ 加载和验证     │   │ 结构和类型   │   │ 生成结构化   │
│                │   │              │   │ 输出         │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 架构说明

**数据流向**：
1. **用户输入** → SkillsManager（通过 Provider 生成 NormalizedIntent Schema）
2. **Intent + Skills** → Director（通过 Provider 生成 DirectorPlan Schema）
3. **Plan + 实时数据** → Cinematographer（生成 CinematographerRecommendation Schema）
4. **Plan + 事件** → Editor（生成 EditPlan Schema）

**Schema 如何提供**：
- 所有 Schema 定义在 `agents_Module/schemas/` 目录
- 使用 Pydantic 确保类型安全和自动验证
- Agent 之间通过 AgentResult 包装传递 Schema 对象

**Provider 如何提供**：
- BaseProvider 接口定义在 `agents_Module/providers/base.py`
- MockProvider（测试）和 BailianProvider（生产）实现该接口
- Orchestrator 初始化时注入到所有 Agent

### 1. Schemas 层（数据模型）

**作用**: 使用 Pydantic 定义所有数据结构，确保类型安全和数据验证

#### 核心 Schema 类型

**SkillManifest** - 技能清单
```python
from agents_Module.schemas import SkillManifest

skill = SkillManifest(
    schema_version="1.0",
    skill_id="portrait_story_director",
    version="0.1.0",
    name="人像故事导演",
    agent_bindings=SkillAgentBindings(
        director=True,
        cinematographer=False,
        editor=False,
        skills_manager=True
    ),
    teaching=SkillTeaching(...),
    rules=[SkillRule(...), ...],
    safety=SkillSafety(...)
)
```

**NormalizedIntent** - 归一化意图
```python
from agents_Module.schemas import NormalizedIntent

intent = NormalizedIntent(
    goal=UserGoal(
        goal_type="portrait_story",
        subject_type="single_portrait",
        style="自然",
        output_goal="头像"
    ),
    output=OutputRequirement(
        ratio="1:1",
        duration_sec=30
    ),
    devices=["insta360_link2", "insta360_x4_air"],
    user_level="beginner"
)
```

**DirectorPlan** - 导演计划
```python
from agents_Module.schemas import DirectorPlan, ShotIntention

plan = DirectorPlan(
    creative_goal="拍摄自然个人肖像",
    priorities=[
        Priority(item="人物表情清晰", reason="社交头像核心要求"),
        Priority(item="避免摆拍感", reason="用户要求自然风格")
    ],
    shot_intentions=[
        ShotIntention(
            stage="establish",
            camera="x4air",
            composition="environmental_wide",
            notes="先展示环境背景"
        )
    ]
)
```

**CinematographerRecommendation** - 摄影建议
```python
from agents_Module.schemas import CinematographerRecommendation

rec = CinematographerRecommendation(
    state="ready",
    shot_strategy=ShotStrategy(
        composition="half_body",
        camera_preference="link2"
    ),
    suggested_actions=[
        SuggestedAction(
            device="link2",
            action="track_face",
            reason="主体稳定且面部清晰"
        )
    ]
)
```

**EditPlan** - 剪辑计划
```python
from agents_Module.schemas import EditPlan, TimelineSegment

edit = EditPlan(
    timeline=[
        TimelineSegment(
            source_id="x4air_001",
            start_ms=0,
            end_ms=3000,
            role="environment_context",
            camera="x4air"
        )
    ],
    render=RenderConfig(
        ratio="9:16",
        quality="high"
    )
)
```

**AgentResult** - 通用结果包装
```python
from agents_Module.schemas import AgentResult, AgentType

result = AgentResult(
    agent=AgentType.DIRECTOR,
    output={"plan": plan_dict},
    success=True,
    errors=[],
    warnings=[],
    teaching_notes=["景别选择原则..."]
)
```

#### Schema 文件结构

```
schemas/
├── __init__.py              # 导出所有 Schema
├── skill.py                 # SkillManifest, SkillRule, SkillAgentBindings
├── intent.py                # NormalizedIntent, UserGoal, SkillQuery
├── plan.py                  # DirectorPlan, ShotIntention, Priority
├── recommendation.py        # CinematographerRecommendation, ShotStrategy
├── edit_plan.py             # EditPlan, TimelineSegment, RenderConfig
├── agent_result.py          # AgentResult, AgentType
├── event.py                 # Event, EventType
└── user_level.py            # UserLevel (Literal type)
```

### 2. Providers 层（模型提供者）

**作用**: 抽象 LLM 调用接口，支持多种模型后端

#### 为什么需要 Provider 层？

Provider 层是 Agent 和 LLM 之间的抽象接口，解决以下问题：

1. **模型切换灵活性** - 可以在 MockProvider（测试）和 BailianProvider（生产）之间无缝切换
2. **结构化输出** - 接收 Pydantic Schema，保证 LLM 返回符合预期的结构化数据
3. **测试友好** - MockProvider 提供确定性输出，无需真实 API 调用
4. **统一接口** - 所有 Agent 使用相同的 `generate()` 方法调用 LLM

#### Provider 如何提供给 Agent？

```python
# 在 Orchestrator 初始化时注入
orchestrator = AgentOrchestrator(
    skill_repository=repository,
    skill_validator=validator,
    model_provider=provider,  # ← 注入 Provider
    audit_log_path="audit.jsonl"
)

# Orchestrator 内部将 Provider 传递给所有 Agent
self.skills_manager = SkillsManagerAgent(
    skill_repository=repository,
    skill_validator=validator,
    model_provider=provider  # ← 传递给 Agent
)
```

#### Provider 接口定义

```python
from abc import ABC, abstractmethod
from typing import Type, Dict, Any
from pydantic import BaseModel

class BaseProvider(ABC):
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        schema: Type[BaseModel],
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用 LLM 并返回结构化输出
        
        Args:
            prompt: 提示词
            schema: Pydantic 模型类（期望的输出结构）
            **kwargs: 额外参数（temperature, max_tokens 等）
            
        Returns:
            符合 schema 的字典，可直接用于初始化 Pydantic 对象
        """
        pass
```

#### MockProvider - 测试用

```python
from agents_Module.providers import MockProvider

provider = MockProvider()

# 自动根据 schema 类型返回预定义的 Mock 数据
result = provider.generate(
    prompt="任何提示词",
    schema=NormalizedIntent
)
# 返回: 符合 NormalizedIntent 结构的字典
intent = NormalizedIntent(**result)
```

**支持的 Schema 类型**:
- `NormalizedIntent` → 返回 Mock 意图数据
- `DirectorPlan` → 返回 Mock 导演计划
- `CinematographerRecommendation` → 返回 Mock 摄影建议
- `EditPlan` → 返回 Mock 剪辑计划
- 其他 Schema → 返回通用 Mock 字典

**MockProvider 的作用**:
1. **无需 API 密钥** - 可以在没有真实 LLM 服务的情况下运行整个工作流
2. **确定性输出** - 每次返回相同的 Mock 数据，适合单元测试
3. **快速迭代** - 不依赖网络请求，加速开发和测试

#### BailianProvider - 百炼模型

```python
from agents_Module.providers import BailianProvider

provider = BailianProvider(
    api_key="your-api-key",
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/api/v1/...",
    timeout=30
)

# 调用真实模型，自动处理 JSON Schema 转换
result = provider.generate(
    prompt="用户想拍摄自然个人肖像",
    schema=NormalizedIntent
)
# 返回: 真实模型生成的结构化字典
intent = NormalizedIntent(**result)
```

**配置方式**:

1. 环境变量（推荐）
```bash
# .env 文件
BAILIAN_API_KEY=sk-ws-...
BAILIAN_MODEL=qwen-plus
BAILIAN_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
```

2. 代码配置
```python
provider = BailianProvider.from_env()  # 自动读取 .env
```

**BailianProvider 的作用**:
1. **生产级调用** - 真实 LLM 生成高质量的结构化输出
2. **Schema 强制** - 将 Pydantic Schema 转换为 JSON Schema，确保模型输出符合要求
3. **错误处理** - 自动重试、超时控制、格式验证

#### Provider 文件结构

```
providers/
├── __init__.py          # 导出 MockProvider, BailianProvider
├── base.py              # BaseProvider 接口
├── mock.py              # MockProvider 实现
└── bailian.py           # BailianProvider 实现
```

### 3. Agent 层（智能体）

每个 Agent 继承 `BaseAgent` 并实现 `process()` 方法：

#### Agent 如何使用 Provider 和 Schema？

```python
from agents_Module.agents import BaseAgent
from agents_Module.schemas import AgentResult, AgentType, DirectorPlan

class DirectorAgent(BaseAgent):
    def __init__(self, model_provider=None):
        super().__init__(AgentType.DIRECTOR, model_provider)
        # ↑ Provider 通过构造函数注入
    
    def process(self, context: Dict[str, Any]) -> AgentResult:
        # 1. 构建提示词
        prompt = self._build_prompt(context)
        
        # 2. 调用 Provider 生成结构化输出
        if self.model_provider:
            # 使用真实 LLM（BailianProvider）
            response = self.model_provider.generate(
                prompt=prompt,
                schema=DirectorPlan  # ← 传入期望的 Schema
            )
        else:
            # 降级为简单逻辑
            response = self._fallback_logic(context)
        
        # 3. 创建 Schema 对象
        plan = DirectorPlan(**response)
        
        # 4. 包装为 AgentResult 返回
        return self._create_result(
            session_id=context["session_id"],
            output=plan,  # ← Schema 对象
            confidence=0.9
        )
```

#### Agent 之间的数据流

```python
# 完整工作流示例
orchestrator = AgentOrchestrator(
    skill_repository=repository,
    skill_validator=validator,
    model_provider=MockProvider()  # ← 注入 Provider
)

# 步骤 1: SkillsManager 使用 Provider 生成 NormalizedIntent Schema
results = orchestrator.run_pre_production(
    user_input="我想拍摄动作挑战视频",
    available_devices=["link2", "x4air"]
)

intent_result = results["intent"]  # AgentResult
intent_schema = intent_result.output  # NormalizedIntent Schema 对象

# 步骤 2: Director 接收 Intent Schema，使用 Provider 生成 DirectorPlan Schema
plan_result = results["plan"]  # AgentResult
plan_schema = plan_result.output  # DirectorPlan Schema 对象

# 步骤 3: Cinematographer 接收 Plan Schema，生成 Recommendation Schema
rec_result = orchestrator.run_filming_step(
    subject={"id": "person_1", ...},
    timestamp_ms=5000
)
rec_schema = rec_result.output  # CinematographerRecommendation Schema 对象

# 步骤 4: Editor 接收 Plan Schema 和事件，生成 EditPlan Schema
edit_result = orchestrator.run_post_production(
    events=[...],
    media_sources=[...]
)
edit_schema = edit_result.output  # EditPlan Schema 对象
```

**关键点**：
- 每个 Agent 的输出都是 **AgentResult**，其中 `output` 字段包含 **Schema 对象**
- Provider 确保 LLM 生成的数据符合 Schema 定义
- Schema 在 Agent 之间传递时保证类型安全

---

### 4. Skills 层（技能系统）

**SkillRepository** - 技能加载与搜索
```python
from agents_Module.skills import SkillRepository

repo = SkillRepository("skills/repository")

# 加载技能
skill = repo.load_skill("portrait_story_director")

# 搜索技能
skills = repo.search(
    tags=["portrait", "story"],
    agent="director",
    max_results=3
)
```

**SkillValidator** - 技能验证
```python
from agents_Module.skills import SkillValidator

validator = SkillValidator()

# 验证技能
is_valid, errors = validator.validate(skill)

# 检查安全约束
if not validator.is_action_allowed(skill, "delete_media"):
    raise SecurityError("Action not allowed")
```

### 5. Orchestration 层（工作流编排）

**AgentOrchestrator** - 协调所有 Agent

```python
from agents_Module.orchestration import AgentOrchestrator

orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=provider
)

# 运行三阶段工作流
# 1. Pre-production: Intent → Skills → Bundle → Plan
pre_results = orchestrator.run_pre_production(...)

# 2. Filming: Real-time recommendations
rec = orchestrator.run_filming_step(...)

# 3. Post-production: Event → Timeline
edit = orchestrator.run_post_production(...)
```

---

## 项目结构

```
agents_Module/
├── agents/                    # 四个核心 Agent
│   ├── base_agent.py         # Agent 基类
│   ├── skills_manager.py     # 意图归一化和技能管理
│   ├── director.py           # 创意规划
│   ├── cinematographer.py    # 实时拍摄建议
│   └── editor.py             # 时间线创建
│
├── skills/                    # 技能系统
│   ├── repository.py         # 技能仓库（加载、搜索、版本管理）
│   ├── validator.py          # 技能验证（安全检查、冲突检测）
│   └── repository/           # 技能存储
│       └── builtin/          # 内置技能
│           ├── portrait_story_director.yaml
│           ├── portrait_composition_coach.yaml
│           └── portrait_reel_editor.yaml
│
├── orchestration/             # 工作流编排
│   └── workflow.py           # AgentOrchestrator 协调器
│
├── providers/                 # 模型提供者抽象层
│   ├── base.py               # BaseProvider 接口
│   ├── mock.py               # MockProvider（用于测试）
│   └── bailian.py            # BailianProvider（百炼模型）
│
├── schemas/                   # Pydantic 数据模型
│   ├── skill.py              # SkillManifest, SkillRule, SkillAgentBindings
│   ├── intent.py             # NormalizedIntent, UserGoal
│   ├── plan.py               # DirectorPlan, ShotIntention
│   ├── recommendation.py     # CinematographerRecommendation
│   ├── edit_plan.py          # EditPlan, TimelineSegment
│   ├── agent_result.py       # AgentResult, AgentType
│   ├── event.py              # Event, EventType
│   └── user_level.py         # UserLevel
│
├── tests/                     # 测试套件
│   ├── conftest.py           # Pytest 配置和 fixtures
│   ├── test_agents.py        # Agent 单元测试
│   ├── test_skills.py        # 技能系统测试
│   ├── test_orchestration.py # 工作流集成测试
│   └── test_real_skills.py   # 真实技能测试
│
├── examples/                  # 示例脚本
│   ├── complete_workflow.py  # 完整工作流示例
│   └── real_skills_demo.py   # 真实技能演示
│
├── cli.py                     # 命令行接口
├── __main__.py               # 模块入口
└── requirements.txt          # Python 依赖
```

---

## 快速开始

### 1. 安装依赖

```bash
cd project00/agents_Module
pip install -r requirements.txt
```

### 2. 运行示例

```bash
# 完整工作流示例
python examples/complete_workflow.py

# 真实技能演示（包含所有测试用例）
python examples/real_skills_demo.py
```

### 3. 使用 CLI

**注意**：CLI 命令有两种运行方式：

**方式 1：在当前目录运行（推荐）**
```bash
# 在 agents_Module 目录内
python cli.py list
python cli.py info portrait_story_director
python cli.py validate portrait_composition_coach
python cli.py run "拍摄自然个人肖像" --mock --verbose
```

**方式 2：作为 Python 模块运行**
```bash
# 在 project00 目录（agents_Module 的父目录）
cd ..
python -m agents_Module list
python -m agents_Module info portrait_story_director
python -m agents_Module validate portrait_composition_coach
python -m agents_Module run "拍摄自然个人肖像" --mock --verbose
```

# 运行工作流（使用真实模型，需要配置 API）
python -m agents_Module run "拍摄南京户外环境人像" --user-level beginner
```

### 4. 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_real_skills.py -v

# 运行特定测试用例
pytest tests/test_real_skills.py::TestU001SingleNaturalAvatar -v
```

---

## 数据流与工作原理

### 完整数据流

```
用户输入
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段 1: Pre-Production (前期制作)                          │
└─────────────────────────────────────────────────────────┘
  │
  ├─► [1] SkillsManager.normalize_intent()
  │        输入: user_input, devices, user_level
  │        输出: NormalizedIntent
  │              ├─ goal: {goal_type, subject_type, style}
  │              ├─ output: {ratio, duration_sec}
  │              └─ query: {tags, agents}
  │
  ├─► [2] SkillsManager.retrieve_skills()
  │        输入: NormalizedIntent.query
  │        处理: SkillRepository.search(tags, agent)
  │        输出: List[SkillManifest]
  │
  ├─► [3] SkillsManager.create_bundle()
  │        输入: skills, intent
  │        处理: SkillValidator.validate()
  │        输出: SkillBundle (validated & merged)
  │
  └─► [4] Director.generate_plan()
           输入: intent, skill_bundle
           输出: DirectorPlan
                 ├─ creative_goal
                 ├─ priorities
                 ├─ shot_intentions (stages)
                 └─ teaching_notes

┌─────────────────────────────────────────────────────────┐
│ 阶段 2: Filming (拍摄中)                                   │
└─────────────────────────────────────────────────────────┘
  │
  └─► [Loop] Cinematographer.recommend()
             输入: director_plan, realtime_subject_state
             输出: CinematographerRecommendation
                   ├─ state (ready/wait/lost)
                   ├─ shot_strategy (composition, camera)
                   ├─ suggested_actions
                   └─ explanation

┌─────────────────────────────────────────────────────────┐
│ 阶段 3: Post-Production (后期制作)                         │
└─────────────────────────────────────────────────────────┘
  │
  └─► Editor.create_timeline()
       输入: events, media_sources, director_plan
       输出: EditPlan
             ├─ timeline (segments with roles)
             ├─ panorama_tracks
             ├─ render (ratio, quality)
             └─ explanations
```

### Schema 转换链

```
String (用户输入)
  ↓ (Provider.call + NormalizedIntent schema)
Dict (JSON from LLM)
  ↓ (Pydantic validation)
NormalizedIntent (typed object)
  ↓ (SkillRepository.search)
List[SkillManifest] (技能列表)
  ↓ (SkillValidator.validate)
SkillBundle (validated bundle)
  ↓ (Provider.call + DirectorPlan schema)
DirectorPlan (导演计划)
  ↓ (传递给 Cinematographer)
CinematographerRecommendation (拍摄建议)
  ↓ (事件检测 + Editor)
EditPlan (剪辑时间线)
```

### Provider 工作原理

```python
# MockProvider: 不调用真实模型，返回预定义数据
provider = MockProvider()
result = provider.call(prompt="任何提示", schema=NormalizedIntent)
# → 直接返回 Mock 的 NormalizedIntent 对象

# BailianProvider: 调用百炼模型 API
provider = BailianProvider(api_key="...", model="qwen-plus")

# 内部流程:
# 1. 将 Pydantic schema 转换为 JSON Schema
json_schema = schema.model_json_schema()

# 2. 构建 API 请求
request = {
    "model": "qwen-plus",
    "input": {"messages": [{"role": "user", "content": prompt}]},
    "parameters": {
        "result_format": "message",
        "response_format": {"type": "json_schema", "json_schema": json_schema}
    }
}

# 3. 发送请求到百炼 API
response = requests.post(api_url, json=request, headers=headers)

# 4. 解析响应并验证
data = response.json()["output"]["choices"][0]["message"]["content"]
result = schema.model_validate_json(data)  # Pydantic 验证

# 5. 返回类型安全的对象
return result  # NormalizedIntent instance
```

---

## 工作流程

### 完整三阶段工作流

```python
from agents_Module.skills import SkillRepository, SkillValidator
from agents_Module.orchestration import AgentOrchestrator
from agents_Module.providers import MockProvider

# 初始化
repo = SkillRepository("skills/repository")
validator = SkillValidator()
provider = MockProvider()

orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=provider
)

# 运行完整工作流
results = orchestrator.run_complete_workflow(
    user_input="我想拍一组自然的个人肖像，用作社交头像",
    available_devices=["insta360_link2", "insta360_x4_air"],
    user_level="beginner",
    events=[
        {"event_type": "environment_start", "timestamp_ms": 0, "duration_ms": 2000},
        {"event_type": "subject_stable", "timestamp_ms": 2000, "duration_ms": 4000},
        {"event_type": "smile", "timestamp_ms": 6000, "duration_ms": 2000}
    ],
    output_requirements={"aspect_ratio": "1:1"}
)

# 检查结果
print(results["pre_production"]["intent"].output)
print(results["pre_production"]["plan"].output)
print(results["post_production"].output)
```

### 分阶段调用

#### 阶段 1: 前期制作（Pre-Production）

```python
# 意图归一化 → 技能检索 → 技能组合 → 导演计划
pre_results = orchestrator.run_pre_production(
    user_input="拍摄南京户外环境人像",
    available_devices=["insta360_link2", "insta360_x4_air"],
    user_level="beginner"
)

# 获取意图
intent = pre_results["intent"].output
# 获取技能组合
bundle = pre_results["bundle"].output
# 获取导演计划
plan = pre_results["plan"].output
```

#### 阶段 2: 拍摄中（Filming）

```python
# 实时拍摄建议
subject_state = {
    "subject_id": "person_001",
    "bbox_normalized": [0.3, 0.2, 0.6, 0.8],
    "face_visible": True,
    "gaze_direction": "left",
    "motion_direction": "still",
    "occlusion_ratio": 0.05,
    "tracking_confidence": 0.92
}

recommendation = orchestrator.run_filming_step(
    current_frame_quality={"exposure": "normal"},
    realtime_subject_state=subject_state
)

print(recommendation.output["shot_strategy"])
print(recommendation.output["suggested_actions"])
```

#### 阶段 3: 后期制作（Post-Production）

```python
# 事件驱动时间线创建
events = [
    {"event_type": "environment_start", "timestamp_ms": 0, "duration_ms": 3000},
    {"event_type": "subject_stable", "timestamp_ms": 3000, "duration_ms": 5000},
    {"event_type": "smile", "timestamp_ms": 8000, "duration_ms": 2000}
]

edit_result = orchestrator.run_post_production(
    events=events,
    output_requirements={"aspect_ratio": "9:16", "duration_target_ms": 10000}
)

timeline = edit_result.output
print(f"Total duration: {timeline['render']['total_duration_ms']}ms")
for shot in timeline['timeline']:
    print(f"{shot['role']}: {shot['start_ms']}-{shot['end_ms']}ms")
```

---

## 技能系统

### 内置技能

#### 1. portrait_story_director（人像故事导演）

服务于 Director Agent，负责拍摄前的人像目标理解：

- 支持：个人肖像、环境人像、采访、多人合影
- 输出：创意目标、镜头优先级、分阶段意图
- 教学：景别选择、人物关系分析、情绪变化保留

#### 2. portrait_composition_coach（人像摄影指导）

服务于 Cinematographer Agent，负责拍摄时的实时建议：

- 支持：景别、构图、眼神空间、运动空间
- 输出：构图建议、跟踪策略、设备选择（仅建议）
- 教学：主体优先级、空间留白原则、逆光处理

#### 3. portrait_reel_editor（人像短片剪辑）

服务于 Editor Agent，负责后期时间线创建：

- 支持：环境镜头、人物主镜头、关系镜头、情绪结果
- 输出：剪辑时间线、全景轨迹、竖屏重构
- 教学：故事弧线、景别变化、反应镜头

### 技能格式

技能使用 YAML 格式定义：

```yaml
schema_version: "1.0"
skill_id: portrait_story_director
version: "0.1.0"
name: 人像故事导演
description: >-
  将用户的人像创作目标转成可执行的导演计划

# Agent 绑定：指定哪些 Agent 可以使用此技能
agent_bindings:
  director: true           # 此技能可被 Director 使用
  cinematographer: false
  editor: false
  skills_manager: true     # SkillsManager 默认可访问所有技能

supported_devices:
  - insta360_x4_air
  - insta360_link2

# 教学层：为初学者提供摄影原理
teaching:
  audience: beginner
  principles:
    - name: 先确定人物关系
      explanation: >-
        人像不是只拍脸。先判断是个人肖像、朋友合影、采访还是环境人像，
        才能决定景别、背景和设备位置。

# 规则层：条件触发的拍摄建议
rules:
  - id: single_portrait_default
    when:
      subject_type: single_portrait
    plan:
      primary_camera: link2
      recommended_shots: [medium_close_up, medium_shot]
    priority: 70
    explanation: >-
      单人肖像优先保证人物表情和眼神清晰，再用少量环境镜头补充人物背景。

# 安全层：白名单动作控制
safety:
  allowed_actions: [suggest_camera_role, suggest_shot_sequence]
  forbidden_actions: [direct_device_control, delete_media]
  requires_human_approval: [change_primary_subject, publish_plan]
```

### 技能操作

```python
from agents_Module.skills import SkillRepository, SkillValidator

repo = SkillRepository("skills/repository")
validator = SkillValidator()

# 加载技能
skill = repo.load_skill("portrait_story_director")

# 搜索技能
skills = repo.search(query="人像", agent="director", max_results=10)

# 验证技能
is_valid, errors = validator.validate(skill)

# 检查冲突
conflicts = validator.check_conflict(skill1, skill2)

# Fork 技能
forked = repo.fork_skill("portrait_story_director", new_author_id="user_123")
```

---

## 测试用例

### 用户测试场景（来自 user_requests.yaml）

#### U001: 自然个人肖像

```
用户输入: "我想拍一组自然的个人肖像，用作社交头像，不要看起来像摆拍。"
预期: subject_type=single_portrait, mood=自然, 避免 forced_pose
```

#### U002: 南京户外环境人像

```
用户输入: "请拍一个人在南京户外环境中的旅行肖像，要让人看出这个地方。"
预期: subject_type=environmental_portrait, primary_camera=x4air
```

#### U003: 人物采访

```
用户输入: "我要录一个人物采访，画面自然、声音清楚，不要剪掉停顿。"
预期: subject_type=interview, preserve_speech=true
```

#### U006: 保留人物反应

```
用户输入: "不要只剪最好看的正脸，我更想保留人物笑出来、朋友反应的画面。"
预期: 优先 emotional_result 和 relationship_context
```

#### U007: 用户不确定景别

```
用户输入: "我不确定该用近景还是全身，你先解释区别，不要直接执行。"
预期: explain_options=true, 不执行设备动作
```

### 运行测试

```bash
# 运行所有真实技能测试
pytest tests/test_real_skills.py -v

# 运行特定用户场景测试
pytest tests/test_real_skills.py::TestU001SingleNaturalAvatar -v
pytest tests/test_real_skills.py::TestU002EnvironmentTravel -v
pytest tests/test_real_skills.py::TestU003Interview -v
```

---

## 配置

### 环境变量（.env）

```bash
# 百炼 API 配置（用于真实模型调用）
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL_NAME=qwen-max

# 技能仓库路径
SKILL_REPOSITORY_PATH=./skills/repository

# 审计日志路径
AUDIT_LOG_PATH=./logs/audit.jsonl
```

### 使用真实模型

```python
from agents_Module.providers.dashscope_provider import DashScopeProvider

# 初始化真实模型提供者
provider = DashScopeProvider(
    api_key="your_api_key",
    model_name="qwen-max"
)

orchestrator = AgentOrchestrator(
    skill_repository=repo,
    skill_validator=validator,
    model_provider=provider  # 使用真实模型
)
```

---

## API 参考

### AgentOrchestrator

主协调器，管理完整工作流。

#### 方法

**`run_complete_workflow()`**
```python
results = orchestrator.run_complete_workflow(
    user_input: str,              # 用户输入
    available_devices: List[str], # 可用设备列表
    user_level: str,              # 用户级别: beginner/intermediate/expert
    events: List[Dict],           # 拍摄事件（可选）
    media_sources: List[str],     # 媒体源（可选）
    output_requirements: Dict     # 输出要求（可选）
)
```

**`run_pre_production()`**
```python
pre_results = orchestrator.run_pre_production(
    user_input: str,
    available_devices: List[str],
    user_level: str = "beginner"
)
# 返回: {"intent": AgentResult, "skills": AgentResult, 
#        "bundle": AgentResult, "plan": AgentResult}
```

**`run_filming_step()`**
```python
recommendation = orchestrator.run_filming_step(
    current_frame_quality: Dict,
    realtime_subject_state: Dict
)
# 返回: AgentResult with cinematographer recommendation
```

**`run_post_production()`**
```python
edit_result = orchestrator.run_post_production(
    events: List[Dict],
    output_requirements: Dict
)
# 返回: AgentResult with edit timeline
```

### SkillRepository

技能仓库管理。

#### 方法

**`load_skill(skill_id, version=None)`** - 加载技能  
**`search(query, tags, agent, device, max_results=10)`** - 搜索技能  
**`save_skill(skill, location="personal")`** - 保存技能  
**`fork_skill(skill_id, new_author_id)`** - Fork 技能  
**`list_all()`** - 列出所有技能

### SkillValidator

技能验证器。

#### 方法

**`validate(skill)`** - 验证技能是否符合规范  
**`can_publish(skill)`** - 检查是否可发布  
**`check_conflict(skill1, skill2)`** - 检测技能冲突

---

## 安全约束

### 动作白名单

Agent 只能执行以下安全动作：

✅ **Director**: `suggest_camera_role`, `suggest_shot_sequence`, `suggest_subject_priority`  
✅ **Cinematographer**: `suggest_composition`, `suggest_tracking`, `suggest_reframe`, `suggest_exposure_check`  
✅ **Editor**: `select_clip`, `suggest_reframe`, `create_subtitle_plan`, `mark_highlight`

### 禁止动作

❌ `delete_media` - 删除媒体  
❌ `format_storage` - 格式化存储  
❌ `firmware_upgrade` - 固件升级  
❌ `execute_shell` - 执行 Shell 命令  
❌ `direct_device_control` - 直接控制设备

### 置信度要求

- 设备建议最低置信度：**0.70**
- 跟踪建议最低置信度：**0.70**
- 场景变更最低置信度：**0.60**

---

## 教学模式

为初学者提供摄影原理解释：

```python
# 在结果中获取教学笔记
if result.teaching_notes:
    for note in result.teaching_notes:
        print(f"📚 {note}")
```

### 教学内容示例

- **景别选择**: "近景强调表情，中景强调人物关系，全身或广角强调人物与环境的关系"
- **眼神空间**: "人物看向哪一侧，通常就在那一侧保留适量空间"
- **运动空间**: "人物正在向前移动时，前方应比身后保留更多空间"
- **故事弧线**: "推荐使用环境建立、人物状态、互动动作、情绪结果四类镜头"

---

## 测试数据

### 测试图片和视频

测试数据位于 `project00/data/test_data/`：

```
data/test_data/
├── img/
│   ├── img1.jpg
│   ├── img2.jpg
│   └── 微信图片_20260922013228_*.jpg  (人像照片)
└── video/
    ├── test_video1.mp4  (人像拍摄视频)
    └── test_video2.mp4  (户外摄影视频)
```

可在测试中引用：

```python
from pathlib import Path

TEST_DATA_ROOT = Path("project00/data/test_data")
TEST_IMG = TEST_DATA_ROOT / "img" / "img1.jpg"
TEST_VIDEO = TEST_DATA_ROOT / "video" / "test_video1.mp4"
```

---

## 审计日志

工作流执行会生成 JSONL 格式的审计日志：

```jsonl
{"session_id": "...", "timestamp": "...", "step": "intent", "result": {...}}
{"session_id": "...", "timestamp": "...", "step": "skills", "result": {...}}
{"session_id": "...", "timestamp": "...", "step": "plan", "result": {...}}
```

查看日志：

```bash
# 查看最近的会话日志
tail -f logs/audit.jsonl

# 使用 jq 解析
cat logs/audit.jsonl | jq 'select(.session_id == "...")'
```

---

## 开发指南

### 添加新技能

1. 创建 YAML 文件：`skills/repository/builtin/{agent_type}/{skill_id}.yaml`
2. 定义 `schema_version`, `skill_id`, `version`, `agent_binding`, `rules`
3. 添加 `teaching` 部分（如果面向初学者）
4. 添加 `safety` 约束
5. 添加 `test_cases`
6. 使用 CLI 验证：`python -m agents_Module validate {skill_id}`

### 添加新 Agent

1. 继承 `BaseAgent` 类
2. 实现 `process(context)` 方法
3. 返回 `AgentResult` 对象
4. 在 `AgentOrchestrator` 中注册
5. 编写单元测试

### 添加新 Provider

1. 实现 `call(prompt, schema)` 方法
2. 返回符合 schema 的结构化输出
3. 支持 Mock 模式用于测试

---

## 常见问题 (FAQ)

### 架构相关

**Q: Schemas 层的作用是什么？**

A: Schemas 使用 Pydantic 定义所有数据结构，提供：
- **类型安全**: 编译时类型检查，IDE 自动补全
- **数据验证**: 自动验证字段类型、范围、必填项
- **JSON 转换**: 自动序列化/反序列化
- **文档生成**: 自动生成 JSON Schema 供 LLM 使用

例如：
```python
from agents_Module.schemas import NormalizedIntent

# 自动验证，类型错误会抛出异常
intent = NormalizedIntent(
    goal={"goal_type": "portrait"},  # 必须符合定义的类型
    output={"ratio": "16:9"},
    devices=["link2"]
)

# JSON Schema 自动生成供 LLM 使用
schema = NormalizedIntent.model_json_schema()
```

**Q: Providers 层解决什么问题？**

A: Providers 抽象了模型调用接口，实现：
- **可测试性**: MockProvider 让测试无需真实 API
- **可替换性**: 轻松切换不同模型后端（百炼、OpenAI、本地模型）
- **统一接口**: 所有 Provider 都实现 `call(prompt, schema)` 方法
- **类型安全**: 返回的是 Pydantic 对象，不是原始字符串

```python
# 开发/测试时使用 Mock
provider = MockProvider()

# 生产环境切换到真实模型
provider = BailianProvider.from_env()

# Agent 代码无需改变
result = provider.call(prompt, schema=NormalizedIntent)
```

**Q: 为什么需要 SkillRepository？**

A: SkillRepository 管理技能的：
- **版本控制**: 支持多版本技能共存
- **搜索过滤**: 按标签、Agent 类型、设备筛选
- **安全验证**: 加载时自动验证安全约束
- **扩展性**: 支持内置、个人、社区技能目录

**Q: agent_bindings 的作用？**

A: `agent_bindings` 控制技能的访问权限：
```yaml
agent_bindings:
  director: true        # Director 可以使用此技能
  cinematographer: false  # Cinematographer 不能使用
  editor: false
  skills_manager: true  # SkillsManager 总是可以访问
```

当 SkillRepository 搜索 `agent="director"` 时，只返回 `director: true` 的技能。

**Q: 为什么 YAML 文件现在使用 agent_bindings 对象而不是 agent_binding 列表？**

A: 这是为了与 Pydantic Schema 对齐：
- **旧格式** (已弃用): `agent_binding: [director, skills_manager]`
- **新格式** (正确): `agent_bindings: {director: true, skills_manager: true}`

Python 代码期望的是对象格式，这样可以直接访问 `bindings.director` 而不是遍历列表。

### 工作流相关

**Q: 三个阶段必须全部执行吗？**

A: 不是。可以单独调用：
```python
# 只运行前期制作
pre_results = orchestrator.run_pre_production(...)

# 只运行拍摄建议（需要先有 plan）
rec = orchestrator.run_filming_step(...)

# 只运行后期制作
edit = orchestrator.run_post_production(...)
```

**Q: MockProvider 返回什么数据？**

A: MockProvider 根据 schema 类型返回预定义的合理数据：
- `NormalizedIntent` → 包含 goal、output、devices 的完整 Intent
- `DirectorPlan` → 包含 creative_goal、priorities、shot_intentions 的计划
- `CinematographerRecommendation` → 包含 shot_strategy 和 suggested_actions
- `EditPlan` → 包含 timeline 和 render 配置

这些数据是硬编码的，但结构完整，可用于测试完整工作流。

**Q: 如何切换到真实模型？**

A: 三步：
1. 创建 `.env` 文件，填入 API Key
```bash
BAILIAN_API_KEY=your-api-key
BAILIAN_MODEL=qwen-plus
```

2. 替换 Provider
```python
from agents_Module.providers import BailianProvider
provider = BailianProvider.from_env()
```

3. 其他代码不变
```python
orchestrator = AgentOrchestrator(..., model_provider=provider)
```

**Q: Agent 如何获取技能内容？**

A: 通过 SkillBundle：
```python
# SkillsManager 检索并验证技能
skills = repository.search(tags=["portrait"], agent="director")
bundle = validator.create_bundle(skills, intent)

# Director 接收 bundle
result = director.process({
    "intent": intent,
    "skill_bundle": bundle  # 包含所有相关技能的 rules、teaching
})
```

Bundle 包含：
- `skills`: 技能列表
- `merged_rules`: 合并后的规则
- `teaching_notes`: 教学内容

### 技能相关

**Q: 如何添加自定义技能？**

A: 
1. 在 `skills/repository/builtin/` 创建 YAML 文件
2. 遵循 schema 格式（参考现有技能）
3. 使用 CLI 验证：
```bash
python -m agents_Module validate my_custom_skill
```

**Q: 技能冲突如何处理？**

A: SkillValidator 检测冲突：
```python
conflicts = validator.check_conflict(skill1, skill2)
# 返回: [{"rule1": "id1", "rule2": "id2", "reason": "..."}]
```

技能可定义 `conflict_policy` 指定解决策略：
```yaml
conflict_policy:
  - conflict: [natural_mood, rapid_highlight_edit]
    resolution: keep_natural_mood
    reason: "用户指定的风格优先"
```

**Q: 技能的 priority 如何工作？**

A: 规则按 priority 排序（0-100），高优先级规则优先应用：
```yaml
rules:
  - id: critical_rule
    priority: 100  # 最高优先级
  - id: normal_rule
    priority: 70   # 中等优先级
```

---

## 故障排除

### 依赖问题

**问题: ModuleNotFoundError: No module named 'pydantic'**

```bash
# 解决方案：安装依赖
pip install -r requirements.txt

# 或单独安装
pip install pydantic>=2.0.0 pyyaml>=6.0 requests>=2.31.0
```

### 技能加载失败

**问题: 技能加载失败，提示 "No valid skills found"**

原因：YAML 文件中 `agent_binding` 格式不正确

```yaml
# ❌ 错误格式（旧版）
agent_binding:
  - director
  - skills_manager

# ✅ 正确格式（当前版本）
agent_bindings:
  director: true
  cinematographer: false
  editor: false
  skills_manager: true
```

**问题: ValidationError: agent_bindings**

检查技能文件是否使用了正确的字段名和格式：

```python
# 检查技能文件
import yaml
with open("skills/repository/builtin/portrait_story_director.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
    print(data.get("agent_bindings"))  # 应该是字典，不是列表
```

### 技能搜索问题

**问题: SkillRepository.search() 只返回第一个 Agent 的技能**

这是已知问题。当前实现中，`_retrieve_skills` 只使用了 Agent 列表的第一个元素：

```python
# 当前代码（skills_manager.py:188）
agent=query.get("agents", [None])[0] if query.get("agents") else None
```

如果需要搜索多个 Agent 的技能，需要循环调用或修改搜索逻辑。

**临时解决方案**：
```python
# 为每个 Agent 单独搜索
all_skills = []
for agent_type in ["director", "cinematographer", "editor"]:
    skills = repository.search(agent=agent_type, tags=tags)
    all_skills.extend(skills)
```

### 验证失败

**问题: 技能验证失败，提示字段缺失**

```bash
# 查看详细错误信息
python -m agents_Module validate portrait_story_director --verbose
```

常见缺失字段：
- `schema_version`: 必须为 "1.0"
- `agent_bindings`: 必须包含所有四个 Agent 的布尔值
- `teaching`: 必须包含 `audience` 和 `principles`
- `safety`: 必须包含 `allowed_actions` 和 `forbidden_actions`

```yaml
# 最小化有效技能
schema_version: "1.0"
skill_id: my_skill
version: "0.1.0"
name: My Skill
description: A valid skill

author:
  type: system_sample
  id: team_name

agent_bindings:
  director: false
  cinematographer: false
  editor: false
  skills_manager: true

teaching:
  audience: beginner
  principles:
    - name: Principle 1
      explanation: Explanation here

inputs:
  required: []
  optional: []

outputs:
  type: agent_result
  required_fields: []

rules: []

safety:
  allowed_actions: []
  forbidden_actions: [direct_device_control, delete_media]
```

### Mock Provider 未返回预期数据

**问题: MockProvider 返回空数据或不匹配的 schema**

检查 schema 类型是否在 MockProvider 的支持列表中：

```python
from agents_Module.providers import MockProvider

provider = MockProvider()

# 查看支持的 schema 类型
print(provider.call("test", schema=NormalizedIntent))  # ✅ 支持
print(provider.call("test", schema=DirectorPlan))      # ✅ 支持
print(provider.call("test", schema=CustomSchema))      # ❌ 返回通用 dict
```

支持的 Schema 类型（见 `providers/mock.py`）：
- `NormalizedIntent`
- `DirectorPlan`
- `CinematographerRecommendation`
- `EditPlan`
- `dict` (fallback)

### Windows 编码问题

**问题: UnicodeEncodeError 'gbk' codec can't encode character**

```bash
# 设置环境变量
set PYTHONIOENCODING=utf-8

# 或在脚本开头添加
import sys
sys.stdout.reconfigure(encoding='utf-8')
```

或将特殊字符替换为 ASCII：
```python
# ✓ → [OK]
# ✗ → [X]
# ⚠️ → [!]
```

### 审计日志问题

**问题: 审计日志路径不存在**

```python
from pathlib import Path

# 确保日志目录存在
log_path = Path("logs/audit.jsonl")
log_path.parent.mkdir(parents=True, exist_ok=True)

orchestrator = AgentOrchestrator(
    ...,
    audit_log_path=str(log_path)
)
```

### API 调用失败（BailianProvider）

**问题: 401 Unauthorized**

检查 API Key 配置：
```bash
# 查看 .env 文件
cat .env

# 确认环境变量已加载
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('BAILIAN_API_KEY'))"
```

**问题: 超时或连接错误**

```python
# 增加超时时间
provider = BailianProvider(
    api_key="...",
    timeout=60  # 默认 30 秒
)
```

**问题: 返回的 JSON 不符合 Schema**

```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看原始响应
provider = BailianProvider(..., debug=True)
```

### 测试失败

**问题: pytest 无法找到模块**

```bash
# 确保 PYTHONPATH 包含项目根目录
export PYTHONPATH="${PYTHONPATH}:F:/BoldMaker/project00"

# 或在测试文件中添加
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**问题: Fixture not found**

检查 `conftest.py` 是否在正确位置：
```
tests/
├── conftest.py          # ← 必须在这里
├── test_agents.py
└── test_skills.py
```

### 性能问题

**问题: 技能搜索缓慢**

```python
# 限制搜索结果数量
skills = repository.search(
    query="portrait",
    max_results=3  # 默认 10
)
```

**问题: Agent 调用超时**

```python
# 使用更快的模型
provider = BailianProvider(
    model="qwen-turbo"  # 而不是 qwen-max
)
```

---

## 许可证

本项目使用 CC-BY-4.0 许可证。

---

## 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m "Add your feature"`
4. 推送到分支：`git push origin feature/your-feature`
5. 提交 Pull Request

---

## 联系方式

- 项目主页: `F:\BoldMaker\project00\agents_Module`
- 技能仓库: `F:\BoldMaker\project00\data\skills`
- 测试数据: `F:\BoldMaker\project00\data\test_data`

---

**ScenePilot Agent Module** - 让 AI 理解摄影，协作创作更好的视觉内容
