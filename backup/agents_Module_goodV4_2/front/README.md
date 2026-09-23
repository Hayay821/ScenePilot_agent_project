# BoldMaker Front 与 ScenePilot API 对接说明

## 启动

后端（同时托管前端和媒体文件）：

```powershell
cd F:\BoldMaker\project00\agents_Module_good
python fast.py serve --mode bailian
```

访问：

```text
http://127.0.0.1:8765/
```

根路径会跳转到 `/app/`，由 FastAPI 托管 `front` 页面；媒体通过 `/media-files/` 提供预览，不需要再启动 5500 静态服务。

测试登录：

```text
账号：test
密码：test
```

## 页面与接口

- `home.html`：读取 `GET /api/v1/media/list`，通过 `/media-files/` 展示 `data/img` 和 `data/video`；支持上传图片/视频到项目 `data`；点击“用于创作”保存路径到浏览器 localStorage。
- `create.html`：直接读取本地素材列表，支持拖拽到工作区的待处理区、视频轨、图片轨和 AI 输出轨；四 Agent 使用工作区素材，多轮输出自动进入 AI 输出轨。
- `skills.html`：读取 `GET /api/v1/skills`，按后端 Skill 的 `id/name/description/stage/tags/path` 展示；添加 Skill 会调用后端保存到 `skills/repository/personal/<stage>/`。
- `cloud.html`：当前仅保留界面，不接云端。

## 为什么浏览器上传不能直接写入 data

仓库页会把浏览器文件转成 data URL，调用 `POST /api/v1/media/upload`，后端持久化到 `data/img` 或 `data/video`。上传完成后刷新素材列表即可选择用于创作。

## 工作区

创作页原“设备连接”区域已经替换为基础工作区：

- 待处理区。
- V1 视频轨。
- V2 图片/叠加轨。
- AI 输出轨。

左侧素材可拖拽到任意轨道，轨道内素材也可拖动到其他轨道。点击素材可在中间预览。

同一个素材可以从素材库反复拖入工作区，每次拖入都会生成独立 `asset_id`；工作区内跨轨移动按 `asset_id` 处理，不会被路径去重阻止。

“保存到仓库”会把工作区结构保存到浏览器 localStorage，素材仓库页会显示工作区生成的视频/图片。

“导出到本地”使用浏览器 File System Access API，让用户选择目录并导出：

- `workspace.json`
- 工作区内可访问的输入图片/视频。
- Agent 生成的抓拍帧和预览视频。

建议使用新版 Chrome 或 Edge。

## AI 输出保存

Agent 生成的抓拍帧、预览视频和结果 JSON 会进入“AI 输出轨”。

- 将 AI 图片/视频从输出轨拖到左侧“本地素材”，前端调用 `POST /api/v1/media/import-output`，把文件复制到 `data/img` 或 `data/video`。
- 在工作区图片/视频上右键，选择“另存为...”，可使用浏览器文件选择器保存到指定目录。
- JSON 输出右键“另存为...”会下载 JSON 文件。
- “保存到素材库”菜单也会把项目输出持久化复制到 `data`。

## Agent 对话附件

素材库和工作区中的图片/视频可以直接拖到右侧 Agent 对话内容区。附件会显示在输入栏上方，并绑定到当前 Agent 会话：

- Director 使用图片附件。
- Cinematographer 使用视频附件并自动抽帧，或直接使用图片。
- Editor 使用全部附件生成时间线和预览。
- SkillsManager 使用对话文本检索 Skill。

首次消息创建会话，后续消息会保留最近的交互摘要和已绑定素材路径。

## 预览失败排查

必须通过 FastAPI 托管页面访问：

```text
http://127.0.0.1:8765/app/
```

不要再从 `http://127.0.0.1:5500` 或 `file://` 打开，因为媒体预览依赖：

```text
/media-files/
/output-files/
```

这两个路径只由 FastAPI 服务提供。

## 拖拽失效排查

拖拽实现同时使用：

- 内存中的当前拖拽对象。
- `application/json`。
- `text/plain`。

支持素材库、工作区轨道和 Agent 对话区之间拖放。

如果浏览器仍表现为旧版本：

1. 使用 `Ctrl+F5` 强制刷新。
2. 确认地址是 `http://127.0.0.1:8765/app/create.html`。
3. 在浏览器控制台执行：

```javascript
localStorage.removeItem('boldmaker_workspace');
location.reload();
```

新版本会自动为旧工作区补齐 `bin/video/image/agent` 四个轨道，但清空旧状态可排除历史数据影响。

## Skill 更新

前端读取后端 `skills/repository` 的索引结果。纯静态页面不能直接写服务器 Skill 数据库。

“添加 Skill”调用 `POST /api/v1/skills`，后端生成符合当前结构的 YAML，保存到 `skills/repository/personal/<stage>/` 并重建索引。
