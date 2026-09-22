# ScenePilot Agent Module 架构更新与修正指南

版本：v1.0  
目标执行者：Claude Coding  
适用目录：`F:\BoldMaker\project00\agents_Module`

## 1. 本次更新目标

在保留当前四 Agent、YAML Skill、Pydantic Schema、Mock/Bailian Provider 和现有测试能力的基础上，修正架构拓扑和数据流，使系统明确体现：

1. `SkillsManager` 是知识准备和 Skill 编译中心。
2. `Director`、`Cinematographer`、`Editor` 按制作阶段运行，不是无条件并行调用。
3. 每个专业 Agent 只接收与自身有关的 Skill Context。
4. Agent 之间只传递经过 Pydantic 验证的结构化对象。
5. 所有决策可追溯到用户意图、Skill 规则和媒体证据。
6. Agent 只给出建议或计划，不直接控制相机、删除素材或执行任意代码。

本次修改是增量修正，不应重写已经通过测试的模块，也不应接入真实相机 SDK。

## 2. 当前架构的问题

当前 README 的核心图将 `SkillsManager`、`Director`、`Cinematographer` 画成并列模块，并共同指向 `Editor`。该图容易造成以下误解：

- 三个 Agent 可以在没有依赖数据的情况下并行执行。
- `SkillsManager` 只完成意图解析，没有用 Skill 指导其他 Agent。
- `Editor` 直接接收前三个 Agent 的任意输出。
- `Cinematographer` 可能直接消费原始视频帧或承担高频检测。
- Skill 检索、合并、冲突裁决和分发之间没有明确边界。

代码中可以保留 Agent 的独立类，但 README 和 Orchestrator 的真实数据流必须改为阶段式。

## 3. 目标架构

```text
用户输入
   |
   v
+---------------------------------------------------+
| AgentOrchestrator                                 |
| 会话状态、阶段切换、上下文裁剪、重试、审计与恢复     |
+---------------------------------------------------+
   |
   v
+---------------------------------------------------+
| SkillsManager Agent                               |
| 1. 归一化用户意图                                  |
| 2. 检索本地/云端 Skill                            |
| 3. 校验、冲突裁决和合并                            |
| 4. 编译 Agent-specific Skill Context              |
| 5. 生成用户教学解释                                |
+---------------------------------------------------+
   |
   | NormalizedIntent + SkillBundle
   v
+---------------------------------------------------+
| Director Agent                                    |
| DirectorSkillContext + Intent + Device Summary    |
| -> DirectorPlan                                   |
+---------------------------------------------------+
   |
   | DirectorPlan
   v
+----------------------+       +--------------------+
| Local Perception     | ----> | RuntimeSceneState  |
| Mock in this phase   |       | EventEvidence      |
+----------------------+       +--------------------+
                                      |
                                      v
+---------------------------------------------------+
| Cinematographer Agent                             |
| CinematographerSkillContext + DirectorPlan        |
| + RuntimeSceneState                               |
| -> CinematographerRecommendation                  |
+---------------------------------------------------+
   |
   | Recommendations + Events + Evidence
   v
+---------------------------------------------------+
| Editor Agent                                      |
| EditorSkillContext + DirectorPlan + EventTimeline |
| + MediaEvidence + OutputRequirements              |
| -> EditPlan                                       |
+---------------------------------------------------+
   |
   v
+---------------------------------------------------+
| PlanValidator / Mock Renderer                     |
| 后续再接 DeviceExecutor 和真实设备桥                |
+---------------------------------------------------+
```

## 4. 必须保持的模块边界

### 4.1 AgentOrchestrator

负责：

- 创建和恢复 Session。
- 注入 Provider、Repository、Validator 和 EvidenceStore。
- 按阶段调用 Agent。
- 保存结构化中间结果。
- 处理超时、重试和 Mock fallback。
- 裁剪传给各 Agent 的上下文。
- 写入审计日志。

不负责：

- 直接写摄影规则。
- 替代 SkillsManager 检索 Skill。
- 直接控制设备。
- 在业务代码中硬编码模型输出。

### 4.2 SkillsManager

负责：

- `normalize_intent()`：将用户语言转换为 `NormalizedIntent`。
- `retrieve_skills()`：根据标签、Agent、设备、场景、许可证和版本检索 Skill。
- `resolve_conflicts()`：识别和处理规则冲突。
- `create_bundle()`：生成经过验证的 `SkillBundle`。
- `compile_contexts()`：为三个专业 Agent 编译专属 Skill Context。
- `explain_skills()`：向用户解释 Skill 原理和选择原因。
- 专家知识转 Skill 草案和发布审批流程，后续增量实现。

不负责：

- 生成最终 DirectorPlan。
- 每帧调用其他 Agent。
- 直接执行相机命令。
- 自动发布 Skill。

### 4.3 Director

负责使用：

- `NormalizedIntent`
- `DirectorSkillContext`
- 设备能力摘要
- 可选历史事件摘要

输出：`DirectorPlan`。

不读取全部 Skill 仓库，不执行设备动作。

### 4.4 Cinematographer

负责使用：

- `DirectorPlan`
- `CinematographerSkillContext`
- `RuntimeSceneState`
- 近期事件摘要

输出：`CinematographerRecommendation`。

它只负责低频策略建议，不负责逐帧目标检测、跟踪、姿态推理或高频 PTZ 控制。本阶段使用 Mock RuntimeSceneState；后续感知层接入时不改变 Agent 接口。

### 4.5 Editor

负责使用：

- `EditorSkillContext`
- `DirectorPlan`
- `EventTimeline`
- `MediaEvidence`
- `OutputRequirements`
- 可选摄影建议和实际执行结果

输出：`EditPlan`。

不直接运行 FFmpeg，不直接删除原始素材。Renderer 属于独立执行层。

## 5. SkillBundle 必须承担指导关系

`SkillsManager` 指导其他三个 Agent 的方式不是反复发送完整 YAML，也不是自然语言对话，而是编译并分发 `SkillBundle`。

建议新增或修正以下 Schema：

```python
class SkillRef(BaseModel):
    skill_id: str
    version: str
    content_hash: str | None = None
    priority: int = 50
    source: Literal["builtin", "local", "cloud", "personal"]


class SkillConflict(BaseModel):
    conflict_id: str
    rule_ids: list[str]
    description: str
    resolution: str | None = None
    requires_user_confirmation: bool = False


class DirectorSkillContext(BaseModel):
    creative_principles: list[dict]
    shot_sequence_rules: list[dict]
    priority_rules: list[dict]
    conflict_resolutions: list[dict]
    teaching_notes: list[str]


class CinematographerSkillContext(BaseModel):
    composition_rules: list[dict]
    tracking_rules: list[dict]
    camera_preference_rules: list[dict]
    confidence_thresholds: dict[str, float]
    allowed_suggestions: list[str]
    teaching_notes: list[str]


class EditorSkillContext(BaseModel):
    selection_rules: list[dict]
    timeline_rules: list[dict]
    panorama_rules: list[dict]
    subtitle_rules: list[dict]
    render_constraints: dict
    teaching_notes: list[str]


class TeachingContext(BaseModel):
    user_level: str
    selected_skill_explanations: list[str]
    photography_terms: dict[str, str]
    decision_explanation_required: bool = True


class SkillBundle(BaseModel):
    bundle_id: str
    intent_id: str
    skills: list[SkillRef]
    director_context: DirectorSkillContext
    cinematographer_context: CinematographerSkillContext
    editor_context: EditorSkillContext
    teaching_context: TeachingContext
    conflicts: list[SkillConflict] = []
    requires_user_confirmation: bool = False
```

如果当前代码已有 `SkillBundle`，优先兼容和迁移，不要新增同名重复模型。

## 6. Skill 冲突优先级

默认优先级：

```text
用户本次明确要求
  > 用户个人 Skill
  > 已审阅的摄影专家 Skill
  > 社区 Skill
  > 系统内置默认 Skill
```

可以自动解决的冲突，应写入 `SkillConflict.resolution`。无法可靠解决时：

```json
{
  "requires_user_confirmation": true,
  "conflicts": [
    {
      "rule_ids": ["natural_slow_cut", "fast_social_rhythm"],
      "description": "自然纪实与快速节奏规则冲突",
      "resolution": null,
      "requires_user_confirmation": true
    }
  ]
}
```

Orchestrator 在用户确认前不得继续生成最终 DirectorPlan。

## 7. 阶段式数据流

### 7.1 Pre-Production

```text
user_input
  -> SkillsManager.normalize_intent()
  -> SkillsManager.retrieve_skills()
  -> SkillValidator.validate()
  -> SkillConflictResolver.resolve()
  -> SkillsManager.create_bundle()
  -> SkillsManager.compile_contexts()
  -> Director.generate_plan()
  -> PlanValidator.validate_director_plan()
```

输出必须保存：

- `NormalizedIntent`
- `SkillBundle`
- `DirectorPlan`
- 验证结果
- 审计日志

### 7.2 Filming

```text
RuntimeSceneState (Mock first)
  + DirectorPlan
  + SkillBundle.cinematographer_context
  -> Cinematographer.recommend()
  -> RecommendationValidator.validate()
  -> EventTimeline / EvidenceStore
```

摄影建议必须包含：

- `timestamp_ms`
- `expires_at_ms`
- `priority`
- `confidence`
- `evidence_refs`
- `skill_rule_refs`
- `requires_executor_validation=true`

过期建议不能继续使用。

### 7.3 Post-Production

```text
EventTimeline
  + MediaEvidence
  + DirectorPlan
  + SkillBundle.editor_context
  + OutputRequirements
  -> Editor.create_timeline()
  -> EditPlanValidator.validate()
  -> Mock Renderer / JSON export
```

输出必须说明每个片段的：

- 来源素材和时间范围。
- 叙事角色。
- 选择理由。
- 证据引用。
- Skill 规则引用。
- 全景片段的 `yaw/pitch/fov`（若适用）。

## 8. 新增基础设施的最小范围

本次只实现最小接口和 Mock，不扩展成复杂平台。

### 8.1 ContextPack

新增 `orchestration/context_pack.py`，用于创建最小必要上下文：

```python
class ContextPack(BaseModel):
    session_id: str
    stage: str
    normalized_intent: NormalizedIntent
    skill_bundle_id: str
    director_plan_id: str | None = None
    recent_event_ids: list[str] = []
    evidence_refs: list[str] = []
```

禁止把完整对话、全部 Skill YAML 和全部视频帧发送给所有 Agent。

### 8.2 EvidenceStore

新增最小的本地 JSONL/文件索引实现：

```text
evidence/
  evidence_store.py
  audit_log.py
```

记录：

- 本地媒体路径与哈希。
- 帧 ID 和时间戳。
- 事件 ID。
- Skill ID/版本/规则 ID。
- Agent 输入输出摘要。
- Provider 和 Prompt 版本。
- 用户批准或拒绝记录。

不得默认把原始图片和视频上传云端。

### 8.3 PlanValidator

新增：

```text
validation/
  plan_validator.py
  safety_validator.py
```

至少检查：

- Pydantic Schema 是否有效。
- 输出动作是否属于 Skill 白名单。
- 是否出现禁止动作。
- 引用的 Skill/规则是否存在。
- 设备能力是否满足，若当前无设备则使用 Mock capabilities。
- 低置信度是否要求人工确认。
- 摄影建议是否已过期。

### 8.4 Perception 边界

本次不要实现完整 YOLO/ByteTrack。只定义：

```text
perception/
  base.py
  mock.py
```

`MockPerceptionProvider` 根据测试场景生成 `RuntimeSceneState` 和 `EventEvidence`。未来接入真实感知时保持 Schema 不变。

## 9. 推荐项目结构

```text
agents_Module/
├── agents/
│   ├── base_agent.py
│   ├── skills_manager.py
│   ├── director.py
│   ├── cinematographer.py
│   └── editor.py
├── skills/
│   ├── repository.py
│   ├── loader.py
│   ├── validator.py
│   ├── merger.py
│   ├── compiler.py
│   └── conflict_resolver.py
├── orchestration/
│   ├── workflow.py
│   ├── workflow_state.py
│   ├── context_pack.py
│   └── retry_policy.py
├── validation/
│   ├── plan_validator.py
│   ├── safety_validator.py
│   └── capability_validator.py
├── evidence/
│   ├── evidence_store.py
│   └── audit_log.py
├── perception/
│   ├── base.py
│   └── mock.py
├── providers/
│   ├── base.py
│   ├── mock.py
│   └── bailian.py
├── schemas/
│   ├── skill.py
│   ├── intent.py
│   ├── context.py
│   ├── plan.py
│   ├── recommendation.py
│   ├── edit_plan.py
│   ├── event.py
│   ├── evidence.py
│   └── agent_result.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── examples/
├── cli.py
├── __main__.py
├── pyproject.toml
└── README.md
```

Skill YAML 数据继续放在：

```text
F:\BoldMaker\project00\data\skills
```

不要复制到代码目录。`agents_Module/skills` 只存加载、验证、合并和编译代码。

## 10. 兼容性和迁移要求

1. 先运行现有测试，记录基线。
2. 不删除当前公共类和 CLI 参数，除非确认无调用方。
3. Schema 变更优先添加默认值或迁移函数。
4. 不保留无具体消费者的兼容分支；只为当前测试、示例和公开接口做迁移。
5. 已存在的 YAML Skill 若字段命名与 Schema 不一致，应由 Loader 正规化并报告 warning，不应静默丢字段。
6. 所有新结构应可 JSON 序列化。
7. 无 `DASHSCOPE_API_KEY` 时全部单元和端到端测试必须使用 Mock 正常运行。
8. 不在本次更新中修改 X4 Air/Link 2 设备桥代码。

## 11. Claude Coding 实施顺序

### Step 0：基线检查

执行并记录：

```text
pytest
python -m agents_Module --help
python examples/complete_workflow.py
```

如果实际命令不同，按项目现有 README 使用。记录失败项，不因架构更新掩盖原有问题。

### Step 1：修正文档图和术语

- 将 README 的并行 Agent 图替换为阶段式图。
- 明确 SkillsManager 通过 `SkillBundle` 指导三个专业 Agent。
- 明确 Cinematographer 不逐帧处理视频。
- 明确 Editor 不负责渲染执行。

### Step 2：补齐 Schema

实现或迁移：

- `SkillRef`
- `SkillConflict`
- `DirectorSkillContext`
- `CinematographerSkillContext`
- `EditorSkillContext`
- `TeachingContext`
- `SkillBundle`
- `ContextPack`
- `RuntimeSceneState`
- `EventEvidence`

为所有 Schema 添加序列化和非法输入测试。

### Step 3：Skill 编译和冲突处理

- 增加 `SkillConflictResolver`。
- 增加 `SkillCompiler` 或扩展现有实现。
- 将完整 Skill 编译为三个专属 Context。
- 规则保留来源 `skill_id/version/rule_id`。
- 用户明确要求拥有最高优先级。

### Step 4：Orchestrator 阶段化

将工作流明确拆分为：

```python
run_pre_production(...)
run_filming_step(...)
run_post_production(...)
```

保留现有 `run_complete_workflow()` 时，应让它调用三个阶段函数，而不是复制逻辑。

### Step 5：Validator、Evidence 和 Mock Perception

- 添加最小 PlanValidator。
- 添加 JSONL EvidenceStore/AuditLog。
- 添加 `MockPerceptionProvider`。
- Agent 输出必须带 Skill 和证据引用。

### Step 6：更新示例和 CLI

示例至少展示：

1. 用户输入被归一化。
2. SkillsManager 找到三个 Skill。
3. SkillBundle 包含三个专属 Context。
4. Director 生成计划。
5. Mock Perception 生成主体稳定、主体丢失或互动事件。
6. Cinematographer 生成有有效期的建议。
7. Editor 生成带证据和规则引用的 EditPlan。

### Step 7：完整测试

运行全部测试，确保 Mock 模式无需外部 API。

## 12. 必须新增的测试

### Unit

- `test_skill_bundle_compiles_agent_contexts`
- `test_user_explicit_rule_has_highest_priority`
- `test_unresolved_conflict_requires_confirmation`
- `test_director_receives_only_director_context`
- `test_cinematographer_receives_only_runtime_summary`
- `test_editor_receives_editor_context_and_evidence`
- `test_forbidden_action_is_rejected`
- `test_expired_recommendation_is_rejected`
- `test_skill_rule_source_is_preserved`

### Integration

- 从 `data/skills` 加载三个人像 Skill。
- 使用 `test_inputs/user_requests.yaml` 生成 Intent 和 Bundle。
- 使用 Mock Provider 跑通三个阶段。
- 检查 AuditLog 包含 session、Skill 版本和 Agent 输出。

### E2E

至少覆盖：

1. 自然个人肖像。
2. 环境旅行人像。
3. 人物采访。
4. 主体丢失时建议使用 X4 Air 全景恢复。
5. 用户修改“突出人物反应”后，Editor 输出发生预期变化。

## 13. 验收标准

- [ ] README 不再把 SkillsManager、Director、Cinematographer 画成无依赖并行关系。
- [ ] SkillsManager 输出包含 `NormalizedIntent` 和 `SkillBundle`。
- [ ] SkillBundle 包含 Director/Cinematographer/Editor 三个专属 Context。
- [ ] Director 只使用 Director Context。
- [ ] Cinematographer 只使用导演计划、摄影 Context 和结构化实时状态。
- [ ] Editor 使用 Editor Context、事件和媒体证据。
- [ ] Skill 冲突有确定优先级或人工确认状态。
- [ ] 每个决策可追溯到 Skill 规则和 Evidence 引用。
- [ ] Agent 不直接控制设备或运行渲染命令。
- [ ] 禁止动作被 Validator 拒绝。
- [ ] Mock Perception 可模拟主体稳定、丢失、遮挡和互动。
- [ ] 无 API Key 可运行全部测试和示例。
- [ ] 现有测试无回归，新增测试通过。

## 14. 非目标

本次不要实现：

- 真实 X4 Air/Link 2 SDK。
- YOLO/ByteTrack 完整实时推理。
- Redis、Kafka 或微服务拆分。
- 公开 Skill 市场后端。
- 任意用户代码执行或 Skill 插件沙箱。
- VideoLLM-online 部署。
- 前端 UI 重构。
- 自动发布专家 Skill。

## 15. 最终架构原则

```text
SkillsManager 编译和分发知识
    -> Director 规划创作目标
    -> Perception 提供结构化现实状态
    -> Cinematographer 生成拍摄策略建议
    -> EvidenceStore 沉淀事件与证据
    -> Editor 生成成片计划
    -> Validator 保证安全与可追溯
```

四个 Agent 的价值来自职责分离和结构化协作，不来自增加模型调用次数。能用规则和本地确定性代码完成的工作，不调用 LLM；只有语义理解、创意规划和解释任务才调用 Provider。
