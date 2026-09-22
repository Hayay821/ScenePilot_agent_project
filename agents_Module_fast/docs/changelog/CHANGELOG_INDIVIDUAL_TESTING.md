# 独立测试功能更新日志

## 更新时间：2026-09-22

## 主要变更

### 1. 模型配置更新

更新为新的 Qwen3 模型：

**视觉模型**：
- `qwen3-vl-flash` - 用于图片和视频分析（Director、Cinematographer、Editor）

**文本模型**：
- `qwen3-vl-plus` - 用于文本理解（SkillsManager）

**`.env` 配置**：
```env
# 模型配置
QWEN_VL_MODEL=qwen3-vl-flash          # 视觉理解模型（多模态）
QWEN_TEXT_MODEL=qwen3-vl-plus         # 文本理解模型

# 各 Agent 专用模型配置
SKILLS_MODEL=qwen3-vl-plus            # SkillsManager: 文本理解
DIRECTOR_MODEL=qwen3-vl-flash         # Director: 图片分析
CINEMATOGRAPHER_MODEL=qwen3-vl-flash  # Cinematographer: 视频帧分析
EDITOR_MODEL=qwen3-vl-flash           # Editor: 素材分析
```

### 2. 新增独立测试脚本

创建了 `test_agents.py`，实现了以下功能：

**输入方式改进**：
- ✅ 每个 Agent 接受单个文件作为输入（不是整个目录）
- ✅ Director: 输入一张参考图片
- ✅ Cinematographer: 输入一个视频文件
- ✅ Editor: 输入一个视频或一张图片

**输出目录独立**：
```
outputs/
├── skills_manager/       # SkillsManager 输出
│   └── skills_director.json
├── director/             # Director 输出
│   └── director.json
├── cinematographer/      # Cinematographer 输出
│   ├── filming.json
│   ├── frames/           # 视频抽帧
│   │   └── test_video1/
│   └── captures/         # 捕获的优质帧
└── editor/               # Editor 输出
    ├── edit_plan.json
    └── preview.mp4
```

**测试命令**：

```bash
# 测试 SkillsManager
python test_agents.py skills --text "我想拍自然的人像" --stage director

# 测试 Director（输入单张图片）
python test_agents.py director --text "请拍摄自然人像" --image data/img/img1.jpg

# 测试 Cinematographer（输入单个视频）
python test_agents.py cinematographer --text "拍摄自然人像" --video data/video/test_video1.mp4

# 测试 Editor（输入单个视频或图片）
python test_agents.py editor --video data/video/test_video1.mp4

# 测试所有 Agent
python test_agents.py all --text "拍摄自然人像" --image data/img/img1.jpg --video data/video/test_video1.mp4
```

### 3. 新增文档

**TEST_INDIVIDUAL_AGENTS.md**：
- 完整的独立测试指南
- 每个 Agent 的测试命令和预期输出
- 输出目录结构说明
- 与原始 `fast.py` 的对比
- 常见问题解决方案
- 验收清单

### 4. README 更新

- 更新模型配置说明
- 添加独立测试脚本使用方法
- 更新各 Agent 使用的模型名称
- 添加 TEST_INDIVIDUAL_AGENTS.md 到文档索引（置顶推荐）
- 更新最小架构说明

## 对比：原始方式 vs 独立测试

### 原始 `fast.py run` 方式

```bash
python fast.py run --mode bailian --text "拍摄人像" --media data
```

**问题**：
- ❌ Director 读取 `data/img/` 下所有图片（最多 6 张）
- ❌ Cinematographer 处理 `data/video/` 下第一个视频
- ❌ Editor 分析 `data/` 下所有素材
- ❌ 所有输出都在 `outputs/` 根目录，混在一起
- ❌ 无法单独测试某个 Agent

### 新的 `test_agents.py` 方式

```bash
# 每个 Agent 独立测试
python test_agents.py director --image data/img/img1.jpg
python test_agents.py cinematographer --video data/video/test_video1.mp4
python test_agents.py editor --video data/video/test_video1.mp4
```

**优势**：
- ✅ 输入明确：每次只输入一个文件
- ✅ 输出独立：每个 Agent 有自己的子目录
- ✅ 易于调试：可以单独测试某个 Agent
- ✅ 结果清晰：不会混在一起
- ✅ 灵活控制：可以选择性地测试部分 Agent

## 向后兼容

- 原始的 `fast.py run` 命令仍然可用
- 原始的 HTTP API 服务仍然可用
- 环境变量配置向后兼容
- 所有现有文档保持有效

## 使用建议

### 推荐使用场景

**使用 `test_agents.py`**（推荐）：
- 开发和调试时
- 测试单个 Agent 的功能
- 验证特定文件的分析结果
- 学习和理解各 Agent 的工作方式

**使用 `fast.py run`**：
- 批量处理多个文件
- 完整的端到端流程测试
- HTTP API 服务

### 快速开始

```bash
# 1. 准备一张图片和一个视频
# data/img/img1.jpg
# data/video/test_video1.mp4

# 2. 测试 Director
python test_agents.py director --mode bailian --text "请拍摄自然人像" --image data/img/img1.jpg

# 3. 查看结果
type outputs\director\director.json

# 4. 测试 Cinematographer
python test_agents.py cinematographer --mode bailian --text "拍摄自然人像" --video data/video/test_video1.mp4

# 5. 查看结果
type outputs\cinematographer\filming.json

# 6. 测试 Editor
python test_agents.py editor --mode bailian --video data/video/test_video1.mp4

# 7. 查看结果
type outputs\editor\edit_plan.json
ffplay outputs\editor\preview.mp4
```

## 验证清单

完成以下检查项：

- [x] `.env` 文件更新为 `qwen3-vl-flash` 和 `qwen3-vl-plus`
- [x] 创建 `test_agents.py` 脚本
- [x] 创建 `TEST_INDIVIDUAL_AGENTS.md` 文档
- [x] 更新 `README.md` 添加独立测试说明
- [x] 更新 `README.md` 中的模型名称
- [x] 创建 `CHANGELOG_INDIVIDUAL_TESTING.md`

## 下一步

1. **准备测试数据**：
   - 确保 `data/img/` 中有图片文件
   - 确保 `data/video/` 中有视频文件

2. **运行测试**：
   ```bash
   # 先用 Mock 模式测试逻辑
   python test_agents.py all --mode mock --image data/img/img1.jpg --video data/video/test_video1.mp4
   
   # 再用 Bailian 模式测试真实 API
   python test_agents.py all --mode bailian --image data/img/img1.jpg --video data/video/test_video1.mp4
   ```

3. **查看输出**：
   ```bash
   # 查看各个 Agent 的输出目录
   dir outputs\skills_manager
   dir outputs\director
   dir outputs\cinematographer
   dir outputs\editor
   ```

4. **验证功能**：
   - SkillsManager 正确匹配中文意图
   - Director 分析参考图片并生成拍摄计划
   - Cinematographer 抽取视频帧并分析画面质量
   - Editor 生成剪辑时间线和预览视频

## 注意事项

1. **模型可用性**：确保你的百炼账号有 `qwen3-vl-flash` 和 `qwen3-vl-plus` 的访问权限
2. **API 额度**：真实模式会消耗 API 额度，测试时注意控制
3. **文件路径**：所有路径参数使用相对路径或绝对路径，Windows 使用反斜杠 `\`
4. **输出清理**：测试前可以清空 `outputs/` 目录，避免旧文件干扰
