# ScenePilot Fast 模型配置更新总结

## 更新内容

本次更新实现了各 Agent 的专用模型配置，优化了性价比和任务匹配度。

## 主要改动

### 1. `.env` 配置增强
新增各 Agent 专用模型环境变量：
- `SKILLS_MODEL=qwen-turbo` - SkillsManager 专用
- `DIRECTOR_MODEL=qwen-vl-plus` - Director 专用
- `CINEMATOGRAPHER_MODEL=qwen-vl-plus` - Cinematographer 专用
- `EDITOR_MODEL=qwen-vl-plus` - Editor 专用

### 2. Provider 类增强
- 新增 `agent_type` 参数，支持按 Agent 类型自动选择模型
- 新增 `text()` 方法，用于纯文本调用（SkillsManager）
- 保留 `vision()` 方法，用于多模态调用（Director、Cinematographer、Editor）
- 实现智能模型选择逻辑：显式指定 > Agent 专用 > 通用配置 > 默认值

### 3. ScenePilotFast 初始化重构
为每个 Agent 创建独立的 Provider 实例：
```python
self.skills_provider = Provider(mode, agent_type="skills")
self.director_provider = Provider(mode, agent_type="director")
self.cinematographer_provider = Provider(mode, agent_type="cinematographer")
self.editor_provider = Provider(mode, agent_type="editor")
```

### 4. 文档更新
- **README.md** - 添加模型选型说明表格
- **QUICK_TEST_GUIDE.md** - 更新配置示例和模型说明
- **MODEL_CONFIGURATION.md** - 新增完整的模型配置指南

## 模型选型理由

| Agent | 模型 | 理由 |
|---|---|---|
| SkillsManager | qwen-turbo | 仅需文本理解，无需视觉能力，成本最优 |
| Director | qwen-vl-plus | 需分析参考图片，多模态性价比最优 |
| Cinematographer | qwen-vl-plus | 需分析视频帧画面，视觉理解核心 |
| Editor | qwen-vl-plus | 需分析视频/图片素材，兼顾效果与成本 |

## 兼容性保证

- 向后兼容：未设置专用模型时，自动降级到通用 `MODEL` 配置
- 环境变量别名支持：`DASHSCOPE_*` / `BAILIAN_*` / `API_*` 三组前缀
- 默认值保护：所有配置项都有合理的默认值

## 使用示例

### 推荐配置（默认）
```env
SKILLS_MODEL=qwen-turbo
DIRECTOR_MODEL=qwen-vl-plus
CINEMATOGRAPHER_MODEL=qwen-vl-plus
EDITOR_MODEL=qwen-vl-plus
```

### 效果优先配置
```env
SKILLS_MODEL=qwen-plus
DIRECTOR_MODEL=qwen-vl-max
CINEMATOGRAPHER_MODEL=qwen-vl-max
EDITOR_MODEL=qwen-vl-max
```

### 成本优先配置
```env
SKILLS_MODEL=qwen-turbo
DIRECTOR_MODEL=qwen-vl-plus
CINEMATOGRAPHER_MODEL=qwen-vl-plus
EDITOR_MODEL=qwen-turbo  # 如果只分析文本时间线
```

## 验证方法

运行以下命令验证配置：

```bash
# 1. 检查环境变量加载
python -c "from fast import Provider; p = Provider('bailian', agent_type='director'); print(f'Director model: {p.model}')"

# 2. 运行完整流程
python fast.py run --mode bailian --text "测试多模型配置" --media data

# 3. 检查输出文件
cat outputs/director.json
cat outputs/filming.json
cat outputs/edit_plan.json
```

## 注意事项

1. **多模态模型要求**：Director、Cinematographer、Editor 必须使用 `qwen-vl-*` 系列，不能使用 `qwen-plus` 等纯文本模型
2. **API Key 必须**：真实模式（`--mode bailian`）必须在 `.env` 中配置有效的 API Key
3. **成本控制**：建议 SkillsManager 使用 `qwen-turbo`，其他 Agent 根据需求选择 `qwen-vl-plus` 或 `qwen-vl-max`

## 下一步

你可以在 conda base 环境中测试：

```bash
cd F:\BoldMaker\project00\agents_Module_fast
python fast.py run --mode bailian --text "请拍摄一组自然的人像短片" --media data
```

检查各 Agent 是否使用了正确的模型，并查看输出结果的质量。
