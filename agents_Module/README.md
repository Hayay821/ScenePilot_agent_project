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
│           ├── director/     # 导演技能
│           │   └── portrait_story_director.yaml
│           ├── cinematographer/  # 摄影指导技能
│           │   └── portrait_composition_coach.yaml
│           └── editor/       # 剪辑技能
│               └── portrait_reel_editor.yaml
│
├── orchestration/             # 工作流编排
│   └── workflow.py           # AgentOrchestrator 协调器
│
├── providers/                 # 模型提供者
│   └── mock.py               # Mock Provider（用于测试）
│
├── schemas/                   # 数据模型
│   ├── agent_types.py        # Agent 类型和结果
│   ├── skill_manifest.py     # 技能清单
│   ├── normalized_intent.py  # 归一化意图
│   ├── director_plan.py      # 导演计划
│   ├── cinematographer_recommendation.py  # 拍摄建议
│   └── edit_plan.py          # 剪辑计划
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

```bash
# 列出所有技能
python -m agents_Module list

# 查看技能详情
python -m agents_Module info portrait_story_director

# 验证技能
python -m agents_Module validate portrait_composition_coach

# 运行工作流（使用 Mock Provider）
python -m agents_Module run "拍摄自然个人肖像" --mock --verbose

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

agent_binding:
  - director
  - skills_manager

supported_devices:
  - insta360_x4_air
  - insta360_link2

teaching:
  audience: beginner
  principles:
    - name: 先确定人物关系
      explanation: >-
        人像不是只拍脸。先判断是个人肖像、朋友合影、采访还是环境人像

rules:
  - id: single_portrait_default
    when:
      subject_type: single_portrait
    plan:
      primary_camera: link2
      recommended_shots: [medium_close_up, medium_shot]
    priority: 70

safety:
  allowed_actions: [suggest_camera_role, suggest_shot_sequence]
  forbidden_actions: [direct_device_control, delete_media]
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

## 故障排除

### 技能加载失败

```python
# 检查技能文件是否存在
from pathlib import Path
skill_path = Path("skills/repository/builtin/director/portrait_story_director.yaml")
print(skill_path.exists())

# 手动加载验证
import yaml
with open(skill_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
    print(data["skill_id"])
```

### 验证失败

```python
# 查看详细错误信息
validator = SkillValidator()
is_valid, errors = validator.validate(skill)
for error in errors:
    print(f"❌ {error}")
```

### Mock Provider 未返回预期数据

```python
# 检查 schema 类型
provider = MockProvider()
print(provider.responses)  # 查看支持的 schema 类型
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
