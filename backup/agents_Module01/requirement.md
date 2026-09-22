# Open Vision 四 Agent 与 Skill 系统设计

版本：v1.0  
适用项目：Open Vision / ScenePilot 开放智能影像系统  
目标设备：Insta360 X4 Air、Insta360 Link 2  
目标实现者：Claude Coding、AI 模块开发成员、摄影知识整理成员

## 1. 目标与边界

本阶段只设计并实现四个 Agent 的模块骨架、Skill 知识结构、本地/云端 Skill 库接口和本地图片/视频测试流程。设备 SDK、云台执行器和完整前端属于后续模块。

四个 Agent：

| Agent | 阶段 | 输入 | 输出 | 能否直接控制设备 |
|---|---|---|---|---|
| 导演 Agent | 拍摄前 | 用户目标、Skills、已有事件时间线 | 导演计划、优先级、冲突裁决 | 否 |
| 摄影指导 Agent | 拍摄时 | 导演计划、设备能力、实时主体状态 | 镜头策略、构图、跟踪和设备动作建议 | 否，只能提议 |
| 剪辑 Agent | 拍摄后 | 事件、素材证据、剪辑 Skill | 时间线、视角轨迹、字幕和成片计划 | 否 |
| Skills 管理 Agent | 全流程、人机交互核心 | 用户语言、图片/视频、Skill 库、专家知识 | 规范化意图、Skill 检索结果、Skill 草案、教学解释和共享申请 | 否 |

### 最重要的权限边界

```text
四个 Agent 只能生成结构化建议或计划
    -> PlanValidator 校验
    -> DeviceExecutor（未来模块）检查能力、权限和安全限制
    -> 设备 SDK/OSC/UVC 执行
```

任何 Agent 都不能直接调用 X4 Air Camera SDK、OSC、Link 2 UVC SDK、Shell、删除文件、格式化存储卡或固件升级接口。

## 2. 产品核心：摄影知识开放共享

Open Vision 的目标不是让 AI 取代摄影师，而是：

- 将摄影专家的经验转化为机器可执行、用户可理解的 Skill。
- 允许专家审阅 AI 对图片或文字建议的提炼结果。
- 由专家决定是否保存、发布和上传 Skill。
- 让初学者能看到“为什么这样拍”，而不仅是得到一个结果。
- 允许用户在专家 Skill 基础上做本地个性化修改。
- 让公开 Skill 在本地和云端之间可同步、可版本化、可撤回。

### 两种互补的学习方向

```text
人学 AI：
摄影专家/教程 -> Skill -> AI 执行并解释 -> 初学者学习摄影逻辑

AI 学人：
用户/专家图片与文字 -> Skills 管理 Agent 提炼 -> 专家审阅批准 -> 本地保存/开源共享
```

这里的“开源共享”在产品实现中应理解为**知识 Skill 的开放共享**，不是默认公开原始照片、视频、人脸或 API 密钥。Skill 与素材必须分离存储，上传前由专家确认授权和隐私状态。

## 3. Skill 应采用什么形式

推荐使用：

1. **YAML/JSON 文件作为可读、可版本控制的 Skill manifest**。
2. **Pydantic/JSON Schema 作为运行时验证协议**。
3. **自然语言 explanation 作为给人看的知识层**。
4. **结构化 rule/action 作为给 Agent 和执行器看的机器层**。
5. **引用的示例图片/视频和专家批注作为可选证据层**。

不要把 Skill 做成一段不可验证的 Prompt。Prompt 只是 Skill 的一个字段。

### 3.1 Skill 分层结构

```text
Skill
  - 身份层：名称、版本、作者、许可证、状态
  - 教学层：适用场景、目标、摄影原理、人类可读解释
  - 输入层：用户参数、媒体类型、设备能力、事件类型
  - 规则层：条件、优先级、冲突解决、禁止行为
  - Agent 层：指导哪个 Agent、何时生效
  - 动作层：建议的构图/跟踪/镜头/剪辑动作
  - 安全层：权限、置信度、人工审批要求、不可做的动作
  - 证据层：示例素材、专家批注、来源和验证结果
  - 版本层：父 Skill、修改记录、审阅状态、发布状态
```

### 3.2 Skill manifest 推荐格式

保存为 `skills/<skill_id>/<version>/skill.yaml`：

```yaml
schema_version: "1.0"
skill_id: action_coach
version: "0.1.0"
name: 动作挑战导演
name_en: Action Coach Director
description: >-
  记录单人动作挑战，保留动作准备、高潮和完成后的反应。
  重点是让初学者理解为什么要保留完整动作弧线。
author:
  type: expert
  id: expert_demo
  display_name: 示例摄影师
license: CC-BY-4.0
visibility: local
status: draft
parent_skill: null

teaching:
  audience: beginner
  principles:
    - "动作类视频需要准备、过程、结果，而不是只截取动作最激烈的一帧"
    - "动作高潮使用更紧的景别，结果反应保留环境和人物关系"
  explain_template: >-
    因为检测到动作开始，所以先保留全身构图；动作达到高潮后再使用更紧的视角；
    动作结束后保留反应，保证观众理解结果。

inputs:
  intent:
    type: object
    properties:
      subject: {type: string}
      activity: {type: string}
      tone: {type: string, enum: [纪录, 热血, 教学, 轻松]}
      output_ratio: {type: string, enum: ["16:9", "9:16", "1:1"]}
  media_types: [image, video, panorama]
  required_capabilities:
    - event_detection

agent_bindings:
  director: true
  cinematographer: true
  editor: true

rules:
  - id: prepare_wide
    when:
      event: action_start
      confidence_gte: 0.70
    advice:
      composition: full_body
      keep_pre_roll_ms: 3000
    priority: 80
    explanation: "动作开始时使用全身构图，让观众理解动作环境和身体关系。"

  - id: action_peak
    when:
      event: action_peak
      confidence_gte: 0.75
    advice:
      camera_preference: link2
      mark_highlight: true
      panorama_reframe: subject_center
    priority: 100
    explanation: "动作高潮是主叙事节点，应优先保留并突出主体。"

  - id: result_reaction
    when:
      event: celebration
      confidence_gte: 0.60
    advice:
      keep_post_roll_ms: 4000
      camera_preference: x4air_if_group_visible
    priority: 70
    explanation: "结果反应提供情绪闭环，并展示人物与队友的关系。"

safety:
  allowed_actions: [suggest_composition, suggest_tracking, mark_highlight, suggest_reframe]
  requires_human_approval: [publish, upload, overwrite_skill]
  forbidden_actions: [delete_media, format_storage, firmware_upgrade]
  min_confidence_for_device_suggestion: 0.75

evidence:
  examples:
    - path: examples/action_01.mp4
      annotations: examples/action_01.json
      note: "动作准备、高潮和庆祝三段"
  expert_notes: []
```

### 3.3 Skill 的四种状态

```text
draft      AI 或用户刚创建，不能公开共享
review     等待专家/用户审阅
published  已批准，可上传云端公共 Skill 库
deprecated 已废弃，仅保留历史版本和迁移提示
```

状态迁移必须由人确认：

```text
draft -> review -> published
draft/review -> local_only
published -> deprecated
```

Skills 管理 Agent 可以生成草案和提交审阅请求，但不能自行把 Skill 发布到云端。

## 4. Skill 库设计

### 4.1 本地 Skill 库

建议目录：

```text
skills/
  builtin/
  community/
  personal/
  pending_review/
  deprecated/
```

使用 SQLite 保存索引，文件保存具体内容：

```text
skills.db
  skill_id
  version
  name
  author_id
  status
  visibility
  tags
  supported_agents
  supported_devices
  content_hash
  created_at
  updated_at
```

### 4.2 云端 Skill 库

云端至少需要以下 API：

```text
GET  /skills/search?q=动作&agent=cinematographer&device=link2
GET  /skills/{skill_id}/versions/{version}
POST /skills/drafts                 上传专家批准后的 Skill
POST /skills/{skill_id}/review      提交审阅状态
POST /skills/{skill_id}/fork        基于公共 Skill 创建个人副本
POST /skills/{skill_id}/report      举报或申请下架
```

云端只存 Skill manifest、教学文本、版本元数据和经过授权的示例素材引用。原始人像/视频不应默认上传。

### 4.3 本地与云端同步策略

- 本地 Skill 可离线使用。
- 云端 Skill 下载到本地后先标记为 `untrusted`，经过 Schema、安全规则和签名校验后才能加载。
- 个人修改使用 fork，不直接覆盖公共版本。
- 同名 Skill 不按文件名覆盖，以 `skill_id + version + content_hash` 区分。
- 云端发布必须由用户明确确认。
- Skill 只能声明白名单动作，不能携带任意 Python、Shell 或 C++ 代码。

## 5. 四 Agent 模块设计

### 5.1 公共模块

四个 Agent 共享以下基础设施：

```text
AgentContext
  - session_id
  - user_profile
  - normalized_intent
  - selected_skills
  - device_capabilities
  - event_timeline
  - media_evidence
  - current_stage

AgentResult
  - agent_name
  - schema_version
  - result_id
  - output
  - evidence_refs
  - explanation
  - confidence
  - warnings
  - requires_human_approval
```

公共基础类：

- `SkillRepository`：本地/云端检索、版本和权限。
- `SkillValidator`：Schema、动作白名单、安全策略。
- `EvidenceStore`：图片、视频帧、事件和文件哈希。
- `PromptRegistry`：每个 Agent 的提示词版本。
- `ModelProvider`：百炼 Qwen、Mock、未来本地模型。
- `AgentOrchestrator`：阶段调度和状态保存。
- `AuditLog`：输入、输出、Skill 版本、模型版本和人工批准记录。

### 5.2 Skills 管理 Agent

这是人机交互核心，但它不是其他三个 Agent 的“老板式自由文本助手”，而是负责生成**规范化意图和 Skill 包**。

#### A. 用户需求转规范化意图

输入：

- “我想拍一个突出动作速度的短片”。
- 用户选择的设备和场景。
- 初学者当前知识水平。

输出：

```json
{
  "intent_id": "intent-001",
  "goal": "action_story",
  "subject": "single_person",
  "priority": ["action_clarity", "peak_moment", "reaction"],
  "style": "热血",
  "output": {"duration_sec": 30, "ratio": "9:16"},
  "skill_query": {
    "tags": ["动作摄影", "全身构图", "高潮", "反应镜头"],
    "agents": ["director", "cinematographer", "editor"]
  },
  "teaching_mode": true
}
```

#### B. Skill 检索和组合

步骤：

1. 解析用户目标和约束。
2. 从本地库检索。
3. 从云端库检索可用版本。
4. 按场景、设备、Agent 绑定、许可证和可信度过滤。
5. 计算相关性：语义匹配 + 标签匹配 + 设备能力匹配 + 用户偏好。
6. 返回最多 3 个候选，不要一次把全部 Skill 塞给其他 Agent。
7. 解释每个候选的适用条件、冲突和需要用户确认的参数。
8. 用户确认后生成 `SkillBundle`。

#### C. 教学模式

当用户是初学者时，Skills 管理 Agent 要把规则翻译成人能理解的语言：

```text
机器规则：composition=full_body when event=action_start
教学解释：动作刚开始时先拍全身，因为观众需要知道人物在哪里、身体如何运动。
你可以选择：
1. 更清楚地展示动作：全身
2. 更强调表情：半身
3. 更强调环境：广角/全景
```

它必须同时返回“执行解释”和“学习解释”，不能只输出术语。

#### D. 专家图片分析

输入可以是：

- 一张专家认为构图优秀的图片。
- 一张失败案例。
- 专家对图片的文字或语音说明。

流程：

1. 视觉模型描述可观察事实：主体位置、前景、背景、线条、光线、景别、视线方向、遮挡和空间关系。
2. 模型提出摄影解释，但明确标注“观察事实”和“推断/建议”。
3. 将专家文字与图片观察对齐。
4. 生成 Skill 草案和若干待确认问题。
5. 用专家能理解的摄影语言反馈：景别、主体关系、视觉引导、负空间、动势、光比、层次、叙事功能。
6. 专家确认、修改或拒绝每条规则。
7. 只有专家明确批准后才进入 `review` 或 `published`。

示例输出：

```json
{
  "observations": [
    {"fact": "主体位于画面右侧三分区域", "confidence": 0.91},
    {"fact": "左侧存在连续道路形成引导线", "confidence": 0.82}
  ],
  "photography_interpretation": [
    {
      "concept": "负空间与视线方向",
      "explanation": "主体朝向左侧，左侧空间为动作/视线预留空间，画面更有前进感。",
      "is_observation": false
    }
  ],
  "skill_draft_rules": [
    {
      "when": "主体运动方向稳定且画面左侧有空间",
      "advice": "保留运动方向前方的负空间",
      "ask_expert": "是否要求主体占画面 1/3 到 1/2？"
    }
  ],
  "expert_decisions_required": ["approve_rule_1", "set_subject_scale"]
}
```

#### E. 专家发布流程

```text
图片/文字/语音输入
    -> 生成观察与 Skill 草案
    -> 专家逐条修改/确认
    -> 本地保存 draft
    -> 专家选择“仅本地”或“申请共享”
    -> 隐私/许可证检查
    -> 用户确认发布
    -> 云端 review/published
```

上传权力必须归专家或 Skill 所有者，Skills 管理 Agent 只能发起申请。

### 5.3 导演 Agent

输入：规范化用户意图、`SkillBundle`、可用设备能力、已有事件时间线（拍摄前可能为空）。

输出：

```json
{
  "plan_id": "plan-001",
  "creative_goal": "突出动作成功和队友反应",
  "priorities": [
    {"name": "action_peak", "weight": 1.0},
    {"name": "reaction", "weight": 0.8}
  ],
  "shot_intentions": [
    {"stage": "prepare", "camera": "x4air", "style": "wide_context"},
    {"stage": "peak", "camera": "link2", "style": "full_body_tracking"},
    {"stage": "reaction", "camera": "x4air", "style": "group_context"}
  ],
  "conflicts": [],
  "decisions": [
    {"rule": "action_peak", "selected": true, "reason": "最高优先级且设备支持"}
  ],
  "teaching_notes": ["动作前保留环境有助于观众理解空间关系"],
  "requires_human_approval": false
}
```

导演 Agent 不关心具体 SDK 函数，也不输出设备控制命令。

### 5.4 摄影指导 Agent

输入：导演计划、设备能力、实时主体状态、当前 Skill 规则、上一轮摄影建议。

输出只允许是建议：

```json
{
  "recommendation_id": "rec-001",
  "state": "tracking",
  "subject": {"id": "person_1", "bbox": [0.30, 0.20, 0.25, 0.65]},
  "shot_strategy": {
    "composition": "full_body",
    "camera_preference": "link2",
    "tracking_speed": "normal",
    "keep_pre_roll_ms": 3000
  },
  "suggested_actions": [
    {
      "device": "link2",
      "action": "set_composition",
      "args": {"style": "full_body"},
      "reason": "动作阶段需要展示身体运动",
      "confidence": 0.88
    }
  ],
  "safety": {"requires_executor_validation": true}
}
```

摄影指导 Agent 不能输出任意代码、URL、Shell 命令或未经批准的设备 API 参数。

### 5.5 剪辑 Agent

输入：事件时间线、视频/图片素材证据、Skill 剪辑规则、导演计划、摄影建议和用户输出要求。

输出：

```json
{
  "edit_plan_id": "edit-001",
  "timeline": [
    {
      "source_id": "x4air_001",
      "start_ms": 12000,
      "end_ms": 16000,
      "role": "prepare",
      "reason": "建立空间和动作前状态"
    },
    {
      "source_id": "link2_001",
      "start_ms": 16000,
      "end_ms": 20500,
      "role": "peak",
      "reason": "动作强度和主体清晰度最高"
    }
  ],
  "panorama_tracks": [
    {"time_ms": 16000, "yaw": 28.0, "pitch": -3.0, "fov": 85.0}
  ],
  "subtitles": [],
  "render": {"ratio": "9:16", "duration_sec": 30},
  "explanations": ["保留准备-高潮-反应三段，形成完整叙事弧线"]
}
```

## 6. Agent 协作关系

```text
用户
  |
  v
Skills 管理 Agent
  |-- 规范化用户意图
  |-- 本地/云端检索和组合 Skill
  |-- 向用户解释 Skill
  |-- 接收专家图片/文字知识
  |-- 生成、审阅、保存、申请发布 Skill
  |
  +--> 导演 Agent（拍摄前）
  |       输出导演计划
  |
  +--> 摄影指导 Agent（拍摄时）
  |       读取导演计划 + 实时状态
  |       输出设备动作建议
  |
  +--> 剪辑 Agent（拍摄后）
          读取事件、证据、剪辑规则
          输出成片计划
```

### 重要：Skills 管理 Agent 不是每次都调用其他 Agent

它负责按阶段准备并缓存上下文：

- 拍摄前：准备 `Intent + SkillBundle` 给导演 Agent。
- 拍摄时：导演计划确定后，只将相关 Skill 规则和计划摘要交给摄影指导 Agent。
- 拍摄后：只将剪辑规则、事件和证据交给剪辑 Agent。

不要把全部 Skill、所有图片和完整对话历史重复发送给每个 Agent。用 `SkillBundle` 和 `ContextPack` 传递最小必要上下文。

## 7. 模块目录建议

```text
agents_Module/
  README.md
  schemas/
    skill.py
    intent.py
    plan.py
    event.py
    agent_result.py
  agents/
    base_agent.py
    skills_manager.py
    director.py
    cinematographer.py
    editor.py
  skills/
    repository.py
    local_repository.py
    cloud_repository.py
    validator.py
    compiler.py
    examples/
  multimodal/
    image_analyzer.py
    video_analyzer.py
    evidence_store.py
  orchestration/
    context_pack.py
    workflow.py
    audit_log.py
  providers/
    base.py
    dashscope.py
    mock.py
  tests/
    fixtures/images/
    fixtures/videos/
    test_skill_schema.py
    test_skill_retrieval.py
    test_expert_ingestion.py
    test_agents_contract.py
    test_workflow_e2e.py
```

建议先使用 Python、Pydantic、pytest 和百炼 OpenAI 兼容客户端。设备桥不进入本阶段 Agent 模块。

## 8. 实现顺序

### Phase 1：先固定协议，不接模型

1. 编写 Skill、Intent、Plan、Recommendation、EditPlan 的 Pydantic Schema。
2. 写 3 个静态 Skill YAML：`ActionCoach`、`TravelStory`、`TeamMoment`。
3. 实现本地 `SkillRepository`。
4. 用 Mock Agent 跑通四 Agent 的输入输出。
5. 用 JSONL 保存每次 Agent 结果和上下文版本。

验收：不依赖网络、不依赖 API Key，完整流程能跑通。

### Phase 2：接入百炼模型

1. 只让 Skills 管理 Agent 先调用 Qwen 做意图规范化和 Skill 检索解释。
2. 再接导演 Agent，要求严格输出 Plan Schema。
3. 再接摄影指导 Agent，输出建议而不是执行命令。
4. 最后接剪辑 Agent，输出时间线和视角轨迹。
5. 所有模型响应经过 Schema 校验和缓存。

验收：模型失败时切换 Mock；模型输出格式错误时不得导致工作流崩溃。

### Phase 3：专家知识提炼

1. 图片分析只输出观察事实、解释、建议三类内容。
2. 专家逐条确认规则。
3. 生成 Skill 草案并保存本地。
4. 专家选择“仅本地保存”或“申请发布”。
5. 发布前检查隐私、许可证、敏感信息和动作白名单。

验收：未经专家确认的 Skill 不能进入 `published`，不能上传云端。

### Phase 4：本地视频测试

1. 读取视频并抽取关键帧。
2. 生成事件时间线或使用人工标注时间线。
3. 将事件与 Skill 规则交给三个工作 Agent。
4. 生成导演计划、摄影建议、剪辑计划。
5. 使用 FFmpeg 或 Mock Renderer 输出预览。

验收：改变 Skill 参数后，至少一个 Agent 输出发生可解释的变化。

## 9. 本地图片测试方案

### 9.1 图片样本目录

```text
tests/fixtures/images/
  composition_rule_of_thirds.jpg
  leading_lines.jpg
  negative_space.jpg
  backlight_failure.jpg
  crowded_scene.jpg
  motion_direction.jpg
```

图片可以来自团队自有拍摄或具有明确授权的公共图片。不要将包含无授权人脸的素材上传云端。

### 9.2 图片测试用例

#### Case I1：构图解释

输入：三分法构图图片。  
专家文字：“我把主体放右边，因为人物正在看向左边。”

期待：

- Skills 管理 Agent 区分“主体位于右侧”这一事实和“为视线预留负空间”这一解释。
- 生成待专家确认的规则，而不是直接发布。
- 用摄影术语和普通语言各输出一份解释。

#### Case I2：失败案例分析

输入：主体靠近画面边缘且运动方向没有空间。  
期待：

- 输出“可能造成运动方向拥挤”的建议。
- 明确这是摄影建议，不伪装成确定事实。
- 生成 `keep_motion_space` Skill 草案。

#### Case I3：专家拒绝

输入：AI 根据一张图片总结“低角度更有力量”。专家选择拒绝。  
期待：

- Skill 保持 `draft` 或标记为 rejected。
- 不能进入本地 active 库，更不能上传云端。
- AuditLog 记录专家拒绝原因。

#### Case I4：专家发布

输入：专家确认所有规则、许可证和隐私状态。  
期待：

- Skill 从 `draft -> review`。
- 用户确认上传后才进入云端。
- 生成版本号和 content hash。

## 10. 本地视频测试方案

### 10.1 视频样本要求

至少准备以下 4 类 10 到 60 秒视频：

| 视频 | 用途 |
|---|---|
| 单人动作：准备-动作-成功-庆祝 | 测试 ActionCoach |
| 人物走动/说话 | 测试 Link 2 跟踪和构图建议 |
| 多人互动 | 测试 TeamMoment 和主体优先级 |
| 360/equirectangular 样片 | 测试 PanoramaReframeSkill |

每个视频同时保存人工事件标注：

```json
{
  "video_id": "action_01",
  "events": [
    {"start_ms": 0, "end_ms": 5000, "type": "prepare"},
    {"start_ms": 5000, "end_ms": 11000, "type": "action_peak"},
    {"start_ms": 11000, "end_ms": 16000, "type": "celebration"}
  ]
}
```

### 10.2 测试流程

```text
本地视频
  -> 抽帧/音频/元数据
  -> STC 或固定采样
  -> 事件时间线
  -> Skills 管理 Agent 选择 Skill
  -> 导演 Agent 生成导演计划
  -> 摄影指导 Agent 生成动作建议
  -> 剪辑 Agent 生成时间线和视角轨迹
  -> Mock Renderer 导出预览
```

### 10.3 视频测试用例

#### Case V1：完整 ActionCoach

期待：

- 导演计划包含准备、高潮、庆祝三个阶段。
- 摄影指导建议动作开始时全身构图。
- 动作高潮标记高光。
- 剪辑计划保留前后片段，而不是只剪高潮的一帧。

#### Case V2：用户修改 Skill

第一次参数：`突出动作技术`。  
第二次参数：`突出队友反应`。

期待：

- 第一次更偏全身和动作轨迹。
- 第二次增加群体/环境视角和庆祝后延长时间。
- 两次结果能指出是哪个 Skill 参数造成了变化。

#### Case V3：设备能力约束

输入：Skill 要求 `full_body`，但设备只支持 `half_body`。  
期待：

- 导演 Agent 或摄影指导 Agent 标记冲突。
- 提供替代方案。
- 不生成越界的真实设备指令。

#### Case V4：低置信度事件

输入：视频中人物被遮挡，模型无法确认动作高潮。  
期待：

- 输出 `unknown` 或低置信度事件。
- 要求人工确认或使用 X4 Air 全景安全方案。
- 不因模型猜测直接标记为高潮。

#### Case V5：全景视角

输入：equirectangular 视频和 `PanoramaReframeSkill`。  
期待：

- 剪辑 Agent 输出 `yaw/pitch/fov` 轨迹。
- 轨迹连续、变化平滑、关联主体证据。
- 能使用 FFmpeg 或 Mock Renderer 生成普通视角预览。

## 11. 测试指标

### Skill 管理指标

- Skill 检索 Top-3 命中率。
- 用户能否理解 Skill 解释并选出正确 Skill。
- 图片事实与推断的区分准确率。
- 专家拒绝后是否阻断发布。
- Skill 版本、作者和许可证是否完整。

### Agent 合同指标

- Schema 合法率 >= 95%。
- 禁止动作泄漏率 = 0。
- 低置信度结果是否触发人工确认。
- 四 Agent 是否保持职责边界。
- 相同输入和 Skill 版本是否能得到可复现结果。

### 视频创作指标

- 人工标注关键事件召回率。
- Top-K 高光人工认可率。
- 用户修改 Skill 后结果是否产生预期变化。
- 视角轨迹是否平滑、主体是否保持在画面可接受区域。
- 从输入素材到导演计划/剪辑计划的延迟。

## 12. Claude Coding 实现提示词

### Prompt 1：先建协议

```text
请在 agents_Module 下创建 Python 模块。先只实现 Pydantic Schema 和 pytest，不接真实模型和设备。定义 SkillManifest、SkillRule、SkillBundle、NormalizedIntent、DirectorPlan、CinematographerRecommendation、EditPlan、AgentResult、AuditEvent。所有 JSON Schema 字段要有测试。
```

### Prompt 2：实现 Skill 库

```text
实现本地 SkillRepository、SkillValidator 和 SkillCompiler。支持从 YAML 读取 Skill，校验 schema_version、agent_bindings、rules、allowed_actions 和 license。禁止执行 Skill 中的任意代码。实现按关键词、Agent、设备和标签检索。添加 ActionCoach、TravelStory、TeamMoment 三个示例。
```

### Prompt 3：实现四个 Mock Agent

```text
实现四个 Agent 类：SkillsManagerAgent、DirectorAgent、CinematographerAgent、EditorAgent。每个 Agent 只读写自己的 Schema，不允许直接调用设备 SDK。先使用 DeterministicMockProvider，让同一输入稳定输出。实现 AgentOrchestrator，按拍摄前、拍摄时、拍摄后阶段运行。
```

### Prompt 4：接入百炼

```text
为四个 Agent 增加 DashScope OpenAI-compatible Provider。模型输出必须经过 Pydantic 校验，失败后重试并切换 Mock。实现请求缓存、超时、最大并发和 prompt 版本记录。不要把 API Key 写入代码、日志或前端。
```

### Prompt 5：图片/视频专家知识提炼

```text
实现 ExpertKnowledgePipeline：输入本地图片、可选专家文字和音频转写，输出 observations、interpretations、skill_draft、questions_for_expert。明确区分观察事实和推断建议。实现专家 approve/reject/edit；只有 approve 后允许保存为 draft/review，只有用户确认后允许上传云端。
```

### Prompt 6：端到端测试

```text
为本地图片和视频 fixtures 编写 pytest。覆盖 Skill 检索、专家拒绝、Skill 发布审批、设备能力冲突、低置信度事件、用户修改 Skill、四 Agent 端到端以及 equirectangular 视角计划。无 API Key 时全部测试必须可运行。
```

## 13. 最小可行实现清单

- [ ] 四个 Agent 类存在且职责独立。
- [ ] 所有 Agent 只返回结构化结果，不直接控设备。
- [ ] Skill 使用 YAML/JSON manifest，而不是单独 Prompt。
- [ ] Skill 有版本、作者、许可证、状态和 content hash。
- [ ] 本地 Skill 库可检索、加载、fork 和回滚。
- [ ] 云端同步接口已抽象，发布必须经过人工确认。
- [ ] Skills 管理 Agent 可以把自然语言转成规范化意图。
- [ ] Skills 管理 Agent 可以分析图片并区分事实/推断。
- [ ] 专家可以逐条批准、修改或拒绝 AI 规则。
- [ ] 初学者可以看到摄影术语解释和普通语言解释。
- [ ] 用户可以定制 Skill 参数并保存个人副本。
- [ ] 本地图片和视频测试夹具存在。
- [ ] Mock 模式无 API Key 可运行。
- [ ] Agent 输出全部经过 Schema 验证。
- [ ] 设备命令只能由后续 DeviceExecutor 执行。
