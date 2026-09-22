# ScenePilot Fast 文档中心

欢迎查看 ScenePilot Fast 的完整文档。本项目是一个轻量级的四 Agent 影像制作原型系统。

---

## 📖 快速导航

### 🚀 入门指南（新手必读）

- **[快速开始](guides/快速开始.md)** ⭐ 最快上手方式
- **[测试所有 Agent](guides/测试所有Agent.md)** ⭐ 完整测试手册
- **[独立测试指南](guides/TEST_INDIVIDUAL_AGENTS.md)** - 单独测试每个 Agent
- **[快速测试手册](guides/QUICK_TEST_GUIDE.md)** - 快速验证流程

### 📚 参考文档

- **[模型配置说明](reference/MODEL_CONFIGURATION.md)** - 模型选择和配置
- **[使用场景说明](reference/USAGE_SCENARIOS.md)** - 测试数据的含义
- **[实现计划](reference/IMPLEMENTATION_PLAN.md)** - 技术实现细节

### 📝 更新日志

- **[模型配置更新日志](changelog/CHANGELOG_MODEL_CONFIG.md)** - 模型配置相关更新
- **[独立测试更新日志](changelog/CHANGELOG_INDIVIDUAL_TESTING.md)** - 测试功能更新

### 📦 历史文档

- **[任务文档](../tasks/)** - 历史任务和需求文档

---

## 🎯 按使用场景查找文档

### 我是新手，第一次使用

1. 阅读 **[快速开始](guides/快速开始.md)** 了解基本安装和配置
2. 运行 `test_all_agents.bat` 快速体验
3. 查看 **[测试所有 Agent](guides/测试所有Agent.md)** 了解每个 Agent 的功能

### 我想测试单个 Agent

1. 阅读 **[独立测试指南](guides/TEST_INDIVIDUAL_AGENTS.md)**
2. 使用 `test_agents.py` 脚本
3. 查看各 Agent 的输出结果

### 我遇到了 API 调用问题

1. 查看 **[模型配置说明](reference/MODEL_CONFIGURATION.md)** 的故障排查部分
2. 检查 `.env` 文件配置
3. 确认 API Key 格式正确（无空格）

### 我想了解技术实现细节

1. 阅读 **[实现计划](reference/IMPLEMENTATION_PLAN.md)**
2. 查看主代码文件：`fast.py`, `*_agent.py`
3. 阅读 Skill 库：`skills/repository/`

---

## 📂 文档结构

```
docs/
├── README.md                    # 本文件 - 文档导航中心
├── guides/                      # 使用指南
│   ├── 快速开始.md              # 新手入门
│   ├── 测试所有Agent.md         # 完整测试手册
│   ├── TEST_INDIVIDUAL_AGENTS.md # 独立测试指南
│   ├── QUICK_TEST_GUIDE.md      # 快速测试
│   └── USAGE_SCENARIOS.md       # 使用场景说明
├── reference/                   # 参考文档
│   ├── MODEL_CONFIGURATION.md   # 模型配置
│   ├── IMPLEMENTATION_PLAN.md   # 实现计划
│   └── USAGE_SCENARIOS.md       # 场景说明
├── changelog/                   # 更新日志
│   ├── CHANGELOG_MODEL_CONFIG.md
│   └── CHANGELOG_INDIVIDUAL_TESTING.md
└── archive/                     # 历史归档
```

---

## 🔗 外部资源

- **根目录 README**: [../README.md](../README.md) - 项目主页
- **Skill 库文档**: [../skills/repository/README.md](../skills/repository/README.md)
- **测试脚本**: `test_agents.py`, `test_all_agents.bat`

---

## 💡 常见问题快速链接

| 问题 | 文档链接 |
|---|---|
| 如何开始使用？ | [快速开始](guides/快速开始.md) |
| 如何测试单个 Agent？ | [独立测试指南](guides/TEST_INDIVIDUAL_AGENTS.md) |
| API 调用失败怎么办？ | [模型配置 - 故障排查](reference/MODEL_CONFIGURATION.md#故障排查) |
| 输出是英文怎么办？ | [测试所有 Agent - 常见问题](guides/测试所有Agent.md#常见问题) |
| data/ 目录的文件是什么？ | [使用场景说明](reference/USAGE_SCENARIOS.md) |
| 如何配置模型？ | [模型配置说明](reference/MODEL_CONFIGURATION.md) |

---

## 📧 获取帮助

如果文档中没有找到答案：

1. 检查各文档的"常见问题"部分
2. 查看更新日志了解最新修复
3. 联系开发团队

---

**最后更新**: 2026-09-22
