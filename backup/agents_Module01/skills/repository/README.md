# 人像 Skill 测试数据

本目录用于测试 Open Vision 的三个工作 Agent：

```text
data/skills/
  director/          拍摄前：导演 Agent 使用
  cinematographer/   拍摄时：摄影指导 Agent 使用
  editor/            拍摄后：剪辑 Agent 使用
  test_inputs/       用户输入和测试预期
```

## Skill 加载规则

- 每个 Skill 的入口文件都是 `skill.yaml`。
- `skill_id`、`version` 和 `content_hash` 用于版本识别；当前样例暂不填写 hash，由加载器计算。
- `agent_binding` 表示该 Skill 主要服务哪个 Agent。
- `rules` 是机器可执行的结构化规则，`teaching` 是给用户看的解释。
- `suggested_actions` 只能生成建议，不能由 Agent 直接调用相机。
- 任何真实设备动作仍需经过 `PlanValidator` 和未来的 `DeviceExecutor`。
- 测试时可以把多个 Skill 合并成一个 `SkillBundle`，传给相应 Agent。

## 样例 Skill

| Agent | Skill | 用途 |
|---|---|---|
| 导演 Agent | `portrait_story_director` | 规划人像拍摄叙事、主体关系和优先级 |
| 摄影指导 Agent | `portrait_composition_coach` | 实时给出景别、构图、跟踪和光线建议 |
| 剪辑 Agent | `portrait_reel_editor` | 从人像素材中生成照片/视频时间线和成片计划 |

## 推荐测试顺序

1. 先加载三个 Skill，检查 YAML 能否通过 Schema 校验。
2. 使用 `test_inputs/user_requests.yaml` 测试用户意图规范化。
3. 选择一个导演 Skill 生成导演计划。
4. 将导演计划和模拟主体状态交给摄影指导 Skill。
5. 将人工事件时间线交给剪辑 Skill。
6. 比较不同用户偏好下的计划差异。
