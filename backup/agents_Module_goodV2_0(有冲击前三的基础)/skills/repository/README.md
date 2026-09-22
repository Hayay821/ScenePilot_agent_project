# 人像 Skill 测试数据

本目录是 ScenePilot Fast 的本地 Skill 数据库，用于指导三个工作 Agent：

```text
skills/repository/
  builtin/director/          拍摄前：导演 Agent 使用
  builtin/cinematographer/   拍摄时：摄影指导 Agent 使用
  builtin/editor/            拍摄后：剪辑 Agent 使用
```

## Skill 加载规则

- 当前 Skill 文件是按 Agent 分类的 YAML 文件；文件名不是协议的一部分。
- `skill_id`、`version` 和 `content_hash` 用于版本识别；当前样例暂不填写 hash，由加载器计算。
- `agent_bindings` 表示该 Skill 主要服务哪个 Agent。
- `rules` 是机器可执行的结构化规则，`teaching` 是给用户看的解释。
- `suggested_actions` 只能生成建议，不能由 Agent 直接调用相机。
- 任何真实设备动作仍需经过 `PlanValidator` 和未来的 `DeviceExecutor`。
- Fast 版本直接将匹配 Skill 的规则摘要传给相应 Agent，不引入复杂 SkillBundle 编译层。

## 样例 Skill

| Agent | Skill | 用途 |
|---|---|---|
| 导演 Agent | `portrait_story_director` | 规划人像拍摄叙事、主体关系和优先级 |
| 摄影指导 Agent | `portrait_composition_coach` | 实时给出景别、构图、跟踪和光线建议 |
| 剪辑 Agent | `portrait_reel_editor` | 从人像素材中生成照片/视频时间线和成片计划 |

## 推荐测试顺序

1. 递归加载 `builtin/**/*.yaml`。
2. 使用中文用户输入匹配英文 tags 或现有中文 tags。
3. 用真实参考图片测试导演规划。
4. 用真实视频抽帧测试摄影指导。
5. 用真实视频/图片测试剪辑时间线和 FFmpeg 预览。
6. 检查规则、安全边界和失败策略。
