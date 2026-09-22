# BoldMaker 本地用户数据服务

## 启动

```bash
cd local_userdata_Module
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8010
```

默认同时托管 `../front`，浏览器访问 `http://127.0.0.1:8010/` 即可。测试账号为 `test / test`。

## 认证

- `POST /api/auth/login`：开发期测试登录，JSON 为 `{"account":"test","password":"test"}`。
- `POST /api/auth/cloud-login`：云端登录完成后传入 `{"uid":"云端uid"}`，用于联调。
- 后续请求使用 `Authorization: Bearer <access_token>`。
- 在 `BOLDMAKER_ALLOW_UID_HEADER=true` 时，也可用 `X-User-Id` 临时联调。生产环境应关闭该选项。

## 接口

- `GET /api/resources`、`POST /api/resources`、`GET/PUT/DELETE /api/resources/{id}`、`GET /api/resources/{id}/content`
- `GET /api/skills`、`POST /api/skills`、`GET/PUT/DELETE /api/skills/{id}`、`GET /api/skills/{id}/content`

上传接口使用 `multipart/form-data`：素材字段名为 `file`，素材 `kind` 可传 `image` 或 `video`；skill 还需要 `name`，可选 `description`、`is_public`。

文件按用户隔离存储，索引和元数据位于 `data/metadata.sqlite3`。当前开发期直接使用经过路径校验的 uid 作为目录名，例如 uid 为 `test` 时使用 `data/users/test/`；`/`、`\\`、`.`、`..` 等非法 uid 会被拒绝。
