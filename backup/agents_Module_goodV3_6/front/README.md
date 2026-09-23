# BoldMaker Front 与 ScenePilot API 对接说明

## 启动

后端：

```powershell
cd F:\BoldMaker\project00\agents_Module_good
python fast.py serve --mode bailian
```

前端静态服务必须从项目根目录启动，这样浏览器才能访问 `data/` 中的预览文件：

```powershell
cd F:\BoldMaker\project00\agents_Module_good
python -m http.server 5500
```

访问：

```text
http://127.0.0.1:5500/front/index.html
```

测试登录：

```text
账号：test
密码：test
```

## 页面与接口

- `home.html`：读取 `GET /api/v1/media/list`，展示 `data/img` 和 `data/video`；点击“用于创作”保存路径到浏览器 localStorage。
- `create.html`：读取已选素材路径，调用 Director/Cinematographer/Editor API。
- `skills.html`：读取 `GET /api/v1/skills`，按后端 Skill 的 `id/name/description/stage/tags/path` 展示。
- `cloud.html`：当前仅保留界面，不接云端。

## 为什么浏览器上传不能直接写入 data

纯静态前端没有权限把本地文件写到服务器的 F 盘目录。当前“添加素材”只在浏览器内创建临时预览，不会持久化，也不能直接传给 Agent。

要让 Agent 使用新文件，当前方式是：

1. 将图片复制到 `data/img/`，或将视频复制到 `data/video/`。
2. 刷新仓库页面。
3. 点击“用于创作”。

真正的浏览器上传需要后端提供 multipart 上传接口；当前按要求未新增该后端功能。

## Skill 更新

前端读取后端 `skills/repository` 的索引结果。纯静态页面不能直接写服务器 Skill 数据库。

“添加 Skill”会下载一个与后端字段兼容的 YAML 草稿。将其放入：

```text
skills/repository/personal/
```

刷新 Skills 页面后即可由后端扫描显示。
