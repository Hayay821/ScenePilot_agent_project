# ScenePilot Fast 模型配置说明

## 模型选型原则

ScenePilot Fast 针对不同 Agent 的任务特点，选择了性价比最优的模型组合：

| Agent | 推荐模型 | 任务特点 | 选型理由 |
|---|---|---|---|
| **SkillsManager** | `qwen-turbo` | 中文意图理解、YAML Skill 匹配 | 轻量高性价比：意图理解相对简单，无需顶级模型或视觉能力。Turbo 版在保证基础推理精度的前提下，能最大程度压缩成本，适合高频调用 |
| **Director** | `qwen-vl-plus` | 用户目标 + 参考图片分析 → 导演计划 | 多模态均衡：需要同时理解文本和参考图片。Plus 版是性价比最高的多模态版本，原生支持图文输入，视觉理解能力强 |
| **Cinematographer** | `qwen-vl-plus` | 视频抽帧分析 → 拍摄建议 | 视觉理解核心：需实时分析画面构图、主体状态。Plus 版在 Vision Arena 榜单中表现优异，能准确判断画面质量并给出专业建议 |
| **Editor** | `qwen-vl-plus` | 视频/图片素材 → 剪辑时间线 | 兼顾效果与成本：时间线规划涉及对素材内容的判断，Plus 版更稳妥；若追求极致成本，可改为 `qwen-turbo`（纯文本场景） |

## .env 配置示例

```env
# API 基础配置
API_KEY=sk-ws-xxx...
API_URL=https://llm-xxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1

# 各 Agent 专用模型（推荐配置）
SKILLS_MODEL=qwen-turbo              # SkillsManager: 轻量文本理解
DIRECTOR_MODEL=qwen-vl-plus          # Director: 多模态图片分析
CINEMATOGRAPHER_MODEL=qwen-vl-plus   # Cinematographer: 视频帧分析
EDITOR_MODEL=qwen-vl-plus            # Editor: 素材分析和时间线

# 默认模型（向后兼容，未指定 Agent 专用模型时使用）
MODEL=qwen-vl-plus
```

## 环境变量优先级

系统会按以下优先级查找配置：

### API Key
1. `DASHSCOPE_API_KEY`
2. `BAILIAN_API_KEY`
3. `API_KEY`

### Base URL
1. `DASHSCOPE_BASE_URL`
2. `BAILIAN_BASE_URL`
3. `API_URL`
4. 默认：`https://dashscope.aliyuncs.com/compatible-mode/v1`

### 模型选择
1. 代码中显式指定的 `model` 参数（最高优先级）
2. Agent 专用模型环境变量：
   - `SKILLS_MODEL`（SkillsManager）
   - `DIRECTOR_MODEL`（Director）
   - `CINEMATOGRAPHER_MODEL`（Cinematographer）
   - `EDITOR_MODEL`（Editor）
3. 通用模型环境变量：
   - `DASHSCOPE_MODEL`
   - `BAILIAN_MODEL`
   - `MODEL`
4. 默认值：`qwen-vl-plus`

## 可用的 Qwen 模型

### 文本模型
- `qwen-turbo` - 最快最便宜，适合简单文本理解
- `qwen-plus` - 平衡性能和成本
- `qwen-max` - 最强文本理解能力

### 多模态模型（Vision）
- `qwen-vl-plus` - 推荐：性价比最高的多模态模型
- `qwen-vl-max` - 最强视觉理解能力，成本较高

**注意**：当前通义千问的 `qwen-plus` 等纯文本模型不支持多模态（图片）输入。Director、Cinematographer、Editor 必须使用 `qwen-vl-*` 系列。

## 成本优化建议

### 极致成本优化
```env
SKILLS_MODEL=qwen-turbo              # 文本理解足够
DIRECTOR_MODEL=qwen-vl-plus          # 多模态必须
CINEMATOGRAPHER_MODEL=qwen-vl-plus   # 多模态必须
EDITOR_MODEL=qwen-turbo              # 如果只分析文本时间线，可降级
```

### 效果优先
```env
SKILLS_MODEL=qwen-plus               # 提升意图理解准确度
DIRECTOR_MODEL=qwen-vl-max           # 最强图片分析
CINEMATOGRAPHER_MODEL=qwen-vl-max    # 最强画面判断
EDITOR_MODEL=qwen-vl-max             # 最强素材理解
```

### 推荐平衡配置（默认）
```env
SKILLS_MODEL=qwen-turbo              # 文本理解成本最优
DIRECTOR_MODEL=qwen-vl-plus          # 多模态性价比最优
CINEMATOGRAPHER_MODEL=qwen-vl-plus   # 多模态性价比最优
EDITOR_MODEL=qwen-vl-plus            # 多模态性价比最优
```

## 运行时模型查看

运行时，系统会打印各 Agent 使用的模型（如果启用了日志）：

```bash
python fast.py run --mode bailian --text "测试" --media data
```

查看输出日志中的模型信息，确认配置生效。

## 命令行覆盖

当前版本不支持命令行参数覆盖模型，所有模型配置必须通过 `.env` 文件或环境变量设置。

如果需要临时测试不同模型，可以：

```bash
# Windows PowerShell
$env:DIRECTOR_MODEL="qwen-vl-max"
python fast.py run --mode bailian --text "测试" --media data

# Linux/Mac
DIRECTOR_MODEL=qwen-vl-max python fast.py run --mode bailian --text "测试" --media data
```

## 故障排查

### 问题：模型不支持图片输入

**错误信息**：`Model 'qwen-plus' does not support vision/image input`

**原因**：使用了纯文本模型处理多模态任务

**解决方案**：
- 确认 `.env` 中 `DIRECTOR_MODEL`、`CINEMATOGRAPHER_MODEL`、`EDITOR_MODEL` 使用 `qwen-vl-*` 系列
- 如果 `MODEL` 设置为 `qwen-plus`，但未设置专用模型，会导致此错误

### 问题：模型不可用

**错误信息**：`Model 'xxx' not available`

**原因**：
- 账号没有该模型的访问权限
- 模型名称拼写错误
- 模型已下线

**解决方案**：
- 登录百炼控制台，确认可用模型列表
- 检查 `.env` 中的模型名称拼写
- 使用推荐的 `qwen-turbo` 和 `qwen-vl-plus`

### 问题：成本过高

**解决方案**：
- SkillsManager 使用 `qwen-turbo`（最便宜）
- Editor 如果只分析文本时间线，可以降级为 `qwen-turbo`
- 减少单次处理的图片数量（默认最多 6 张）
- 降低视频抽帧频率（默认 2 秒一帧）

## 未来扩展

### 支持其他模型提供商

当前架构支持扩展到其他 OpenAI 兼容的 API：

```env
# 示例：使用 OpenAI GPT-4V
API_URL=https://api.openai.com/v1
API_KEY=sk-xxx...
DIRECTOR_MODEL=gpt-4-vision-preview
```

### 自定义模型映射

未来可以支持更灵活的模型选择策略，例如根据任务复杂度动态选择模型。

## 参考资源

- [阿里云百炼模型列表](https://help.aliyun.com/zh/model-studio/getting-started/models)
- [通义千问 API 文档](https://help.aliyun.com/zh/dashscope/developer-reference/api-details)
- [OpenAI 兼容接口说明](https://help.aliyun.com/zh/dashscope/developer-reference/compatibility-of-openai-with-dashscope)
