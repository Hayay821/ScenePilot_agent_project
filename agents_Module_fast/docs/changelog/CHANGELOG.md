# 更新日志

## v1.2 - 专家技能创作系统 (2024-01-15)

### 🎉 新增功能

#### 1. 专家技能创作功能

允许专业摄影师通过自然语言输入分享经验，系统自动提取为结构化的拍摄技能。

**核心特性**：
- 🤖 **AI 自动提取**：使用 LLM 将自然语言转化为结构化 YAML
- 📋 **交互式审核**：用户可选择保存到 personal/builtin 或取消
- 🔄 **智能合并**：自动检测相似技能并支持规则合并
- 📊 **索引管理**：自动维护技能索引表，快速检索和更新

**使用示例**：
```bash
python test_agents.py skills-author \
  --mode bailian \
  --expert-input "拍摄人像时，我会让模特面向主光源，确保眼睛有眼神光。"
```

#### 2. 扩展的目录结构

```
skills/repository/
├── builtin/               # 内置技能库
│   ├── common/           # ✨ 新增：通用技能
│   ├── director/
│   │   ├── portrait/
│   │   ├── landscape/    # ✨ 新增：风景
│   │   ├── product/      # ✨ 新增：产品
│   │   └── sports/       # ✨ 新增：运动
│   ├── cinematographer/
│   └── editor/
├── personal/             # ✨ 新增：个性化技能库
├── pending_review/       # ✨ 新增：待审核技能
└── skill_index.json      # ✨ 新增：技能索引表
```

#### 3. 新增技能模板

新增 5 个跨场景的技能模板：
- **golden_hour_landscape.yaml** - 黄金时刻风景拍摄
- **clean_product_director.yaml** - 清晰产品摄影规划
- **action_sports_tracking.yaml** - 运动摄影跟踪
- **universal_composition.yaml** - 通用构图原则
- **landscape_narrative_editor.yaml** - 风景叙事剪辑

#### 4. 技能索引系统

**skill_index.json** 自动记录所有技能：
```json
{
  "skill_id": {
    "path": "相对路径",
    "stage": "director/cinematographer/editor/common",
    "category": "portrait/landscape/product/sports/common",
    "source": "builtin/personal/pending_review",
    "last_updated": "2024-01-15T12:30:00Z"
  }
}
```

### 🔧 API 变更

#### SkillManager 类

**新增方法**：
- `_ensure_directories()` - 自动创建扩展的目录结构
- `_load_or_create_index()` - 加载或创建索引表
- `_rebuild_index()` - 重建索引表
- `_save_index()` - 保存索引到磁盘
- `get_skill_path(skill_id)` - 通过 ID 获取技能路径
- `update_index(skill_id, path, stage, category, source)` - 更新索引
- `extract_skill_from_text(expert_text, provider)` - 从自然语言提取技能
- `find_similar_skill(new_skill)` - 查找相似的现有技能
- `merge_skill_rules(existing_path, new_skill)` - 合并技能规则
- `save_skill(skill_data, destination, merge_if_exists)` - 保存技能到目标库

#### SkillsManagerAgent 类

**新增方法**：
- `author_from_expert(expert_text)` - 专家技能创作主入口
- `review_and_save(skill_id, destination)` - 交互式审核和保存

**修改方法**：
- `interact()` - 返回字段从 `skills` 改为 `matched_skills`（保持兼容）

### 📝 文档更新

**新增文档**：
- `docs/guides/专家技能创作指南.md` - 完整的功能使用指南

**更新文档**：
- `README.md` - 添加新功能说明和文档链接
- `test_agents.py` - 新增 `skills-author` 测试命令

### 🐛 Bug 修复

- 修复索引表在首次运行时不存在的问题
- 修复技能合并时可能的重复规则问题
- 改进错误处理和用户提示

### 💡 技术改进

- **类型安全**：新增 `Literal` 类型提示（"personal", "builtin", "cancel"）
- **时间戳管理**：使用 ISO 格式记录创建和更新时间
- **自动化**：目录结构和索引表自动初始化
- **容错性**：索引损坏时自动重建

### 📊 统计

- 新增代码行数：约 400 行
- 新增测试命令：1 个（`skills-author`）
- 新增 YAML 模板：5 个
- 新增文档：1 个（5000+ 字）

---

## v1.1 - Agent 模块化重构 (2024-01-10)

### 主要变更

- 将所有 Agent 代码迁移到 `agents/` 子目录
- 每个 Agent 有独立的子目录和模块
- 所有 Agent 在执行前会先调用 SkillsManager
- 用户可见的 Skills 匹配和应用反馈

---

## v1.0 - 初始版本 (2024-01-01)

### 核心功能

- 四个 Agent：SkillsManager、Director、Cinematographer、Editor
- 支持百炼 Qwen-VL 多模态模型
- 本地媒体处理（图片、视频）
- 结构化 JSON 输出
- 中英文交互支持
