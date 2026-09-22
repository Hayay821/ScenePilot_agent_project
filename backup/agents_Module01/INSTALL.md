# 快速安装和测试指南

## 方法 1: 开发模式安装（推荐）

在 `agents_Module` 目录下运行：

```bash
# 进入目录
cd F:\BoldMaker\project00\agents_Module

# 开发模式安装（可编辑模式）
pip install -e .

# 或者只安装依赖
pip install -r requirements.txt
```

安装后可以直接使用：

```bash
# 运行测试
pytest tests/test_real_skills.py -v

# 运行示例
python examples/real_skills_demo.py

# 使用 CLI
python -m agents_Module list
```

## 方法 2: 不安装，直接运行

如果不想安装，可以直接运行（脚本已经添加了路径设置）：

```bash
cd F:\BoldMaker\project00\agents_Module

# 运行示例（已经包含 sys.path 设置）
python examples/real_skills_demo.py
python examples/complete_workflow.py

# 运行测试（conftest.py 已经包含 sys.path 设置）
pytest tests/test_real_skills.py -v
pytest tests/ -v
```

## 方法 3: 设置 PYTHONPATH

### Windows CMD:
```cmd
set PYTHONPATH=F:\BoldMaker\project00
cd F:\BoldMaker\project00\agents_Module
pytest tests/test_real_skills.py -v
```

### Windows PowerShell:
```powershell
$env:PYTHONPATH="F:\BoldMaker\project00"
cd F:\BoldMaker\project00\agents_Module
pytest tests/test_real_skills.py -v
```

### Git Bash / Linux / macOS:
```bash
export PYTHONPATH=/f/BoldMaker/project00
cd /f/BoldMaker/project00/agents_Module
pytest tests/test_real_skills.py -v
```

## 验证安装

运行以下命令验证安装是否成功：

```bash
# 测试导入
python -c "from agents_Module.skills import SkillRepository; print('✓ Import successful')"

# 列出技能
python -m agents_Module list

# 运行快速测试
pytest tests/test_agents.py::test_skills_manager_normalize_intent -v
```

## 常见问题

### 问题 1: ModuleNotFoundError: No module named 'agents_Module'

**原因**: Python 找不到 agents_Module 包

**解决方案**:
1. 使用开发模式安装: `pip install -e .`
2. 或者设置 PYTHONPATH（参见方法 3）
3. 脚本已经添加了 `sys.path.insert(0, ...)` 来自动处理路径

### 问题 2: No module named 'pydantic' / 'yaml' / 'pytest'

**原因**: 缺少依赖包

**解决方案**:
```bash
pip install -r requirements.txt
```

### 问题 3: 技能文件找不到

**原因**: 技能仓库路径不正确

**解决方案**:
```python
# 在代码中使用绝对路径
from pathlib import Path
repo_path = Path(__file__).parent / "skills" / "repository"
repo = SkillRepository(str(repo_path))
```

## 推荐的工作流程

### 开发和测试

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 安装包（开发模式）
pip install -e .

# 3. 运行所有测试
pytest tests/ -v

# 4. 运行特定测试
pytest tests/test_real_skills.py::TestU001SingleNaturalAvatar -v

# 5. 运行示例
python examples/real_skills_demo.py
```

### 使用 CLI

```bash
# 列出所有技能
python -m agents_Module list

# 搜索人像技能
python -m agents_Module list --query 人像

# 查看技能详情
python -m agents_Module info portrait_story_director

# 验证技能
python -m agents_Module validate portrait_composition_coach

# 运行工作流（Mock 模式）
python -m agents_Module run "拍摄自然个人肖像" --mock --verbose
```

## 项目结构确认

确保目录结构正确：

```
project00/
├── agents_Module/
│   ├── __init__.py          ✓ 必须存在
│   ├── agents/
│   │   └── __init__.py      ✓ 必须存在
│   ├── skills/
│   │   ├── __init__.py      ✓ 必须存在
│   │   └── repository/
│   │       └── builtin/
│   │           ├── director/
│   │           │   └── portrait_story_director.yaml
│   │           ├── cinematographer/
│   │           │   └── portrait_composition_coach.yaml
│   │           └── editor/
│   │               └── portrait_reel_editor.yaml
│   ├── orchestration/
│   │   └── __init__.py      ✓ 必须存在
│   ├── providers/
│   │   └── __init__.py      ✓ 必须存在
│   ├── schemas/
│   │   └── __init__.py      ✓ 必须存在
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_real_skills.py
│   ├── examples/
│   │   ├── complete_workflow.py
│   │   └── real_skills_demo.py
│   ├── requirements.txt
│   └── setup.py
```

## 下一步

安装成功后，可以：

1. **运行测试**: `pytest tests/ -v`
2. **查看示例**: `python examples/real_skills_demo.py`
3. **使用 CLI**: `python -m agents_Module list`
4. **开始开发**: 查看 [README.md](README.md) 了解 API 使用

---

**问题反馈**: 如果遇到其他问题，请检查 Python 版本（需要 >= 3.9）和依赖是否正确安装。
