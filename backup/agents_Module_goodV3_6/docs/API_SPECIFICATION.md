# ScenePilot Fast API 接口规范文档

## 概述

本文档定义了 ScenePilot Fast 多智能体系统的标准化 RESTful API 接口规范，用于前端对接。

**版本**: v1.0  
**最后更新**: 2026-09-23

---

## 目录

1. [通用规范](#通用规范)
2. [数据模型](#数据模型)
3. [媒体输入接口](#媒体输入接口)
4. [Agent 接口](#agent-接口)
5. [Skills 管理接口](#skills-管理接口)
6. [WebSocket 实时接口](#websocket-实时接口)
7. [错误处理](#错误处理)

---

## 通用规范

### Base URL
```
http://localhost:8765/api/v1
```

### 请求头
```http
Content-Type: application/json
Accept: application/json
```

### 响应格式
所有接口统一返回 JSON 格式：

**成功响应**:
```json
{
  "success": true,
  "data": { ... },
  "agent_type": "director|cinematographer|editor|skills_manager",
  "timestamp": "2026-09-23T10:30:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "详细错误描述",
    "details": { ... }
  },
  "timestamp": "2026-09-23T10:30:00Z"
}
```

### HTTP 状态码
- `200 OK`: 成功
- `201 Created`: 创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器错误

---

## 数据模型

### MediaSourceType（媒体源类型）

```python
enum MediaSourceType:
  - FILE        # 本地文件路径
  - WEBCAM      # 本地摄像头
```

### MediaInput（媒体输入）

**文件输入**:
```json
{
  "source_type": "FILE",
  "paths": [
    "/path/to/image1.jpg",
    "/path/to/video.mp4"
  ]
}
```

**摄像头输入**:
```json
{
  "source_type": "WEBCAM",
  "camera_config": {
    "camera_id": 0,
    "frame_interval": 1.0,
    "max_duration": 30.0,
    "resolution": [1280, 720]
  }
}
```

### SkillsFilter（技能筛选）

```json
{
  "stage": "director|cinematographer|editor",
  "tags": ["portrait", "natural_light"],
  "limit": 5
}
```

### OutputConfig（输出配置）

```json
{
  "output_dir": "/path/to/output",
  "save_intermediate": true,
  "formats": ["json", "preview"]
}
```

---

## 媒体输入接口

### 1. 获取媒体信息

**端点**: `GET /media/info`

**查询参数**:
```
?path=/path/to/media/file.mp4
```

**响应**:
```json
{
  "success": true,
  "data": {
    "path": "/path/to/file.mp4",
    "type": "video",
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "frames": 900,
    "duration": 30.0
  }
}
```

### 2. 列出目录媒体文件

**端点**: `GET /media/list`

**查询参数**:
```
?directory=/path/to/media&type=images|videos|all
```

**响应**:
```json
{
  "success": true,
  "data": {
    "images": ["/path/to/img1.jpg", "/path/to/img2.png"],
    "videos": ["/path/to/vid1.mp4"],
    "total": 3
  }
}
```

### 3. 提取视频帧

**端点**: `POST /media/extract-frames`

**请求体**:
```json
{
  "video_path": "/path/to/video.mp4",
  "output_dir": "/path/to/frames",
  "every_seconds": 2.0,
  "max_frames": 12
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "frames": [
      "/path/to/frames/frame_000000.jpg",
      "/path/to/frames/frame_000060.jpg"
    ],
    "total": 12
  }
}
```

### 4. 从摄像头捕获帧

**端点**: `POST /media/capture-webcam`

**请求体**:
```json
{
  "camera_id": 0,
  "num_frames": 5,
  "interval": 1.0,
  "output_dir": "/path/to/captures",
  "resolution": [1280, 720]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "frames": [
      "/path/to/captures/webcam_0_frame_0.jpg",
      "/path/to/captures/webcam_0_frame_1.jpg"
    ],
    "camera_id": 0,
    "total": 5
  }
}
```

---

## Agent 接口

### 1. Director Agent（导演智能体）

**端点**: `POST /agents/director`

**请求体**:
```json
{
  "user_text": "拍摄一个自然光人像视频",
  "media_input": {
    "source_type": "FILE",
    "paths": ["/path/to/ref1.jpg", "/path/to/ref2.jpg"]
  },
  "skills_filter": {
    "stage": "director",
    "limit": 3
  },
  "output_config": {
    "output_dir": "/path/to/output"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "goal": "拍摄一个自然光人像视频",
    "matched_skills": ["skill_001", "skill_002"],
    "skills_guidance": "应用自然光人像技巧...",
    "shot_plan": [
      {
        "stage": "establish",
        "shot": "wide_context",
        "reason": "建立环境背景"
      },
      {
        "stage": "subject",
        "shot": "medium_portrait",
        "reason": "聚焦主体"
      }
    ],
    "reference_analysis": [
      {
        "image_index": 0,
        "summary": "自然光从左侧射入",
        "composition": "中景人像",
        "lighting": "柔和自然光",
        "subject_position": "画面右侧三分之一",
        "emotional_tone": "平静自然"
      }
    ],
    "confidence": 0.85,
    "user_summary_zh": "已生成拍摄前导演方案"
  },
  "agent_type": "director",
  "timestamp": "2026-09-23T10:30:00Z"
}
```

### 2. Cinematographer Agent（摄影师智能体）

**端点**: `POST /agents/cinematographer`

**请求体（文件输入）**:
```json
{
  "user_text": "分析当前画面构图",
  "media_input": {
    "source_type": "FILE",
    "paths": [
      "/path/to/frame1.jpg",
      "/path/to/frame2.jpg"
    ]
  },
  "skills_filter": {
    "stage": "cinematographer"
  }
}
```

**请求体（摄像头输入）**:
```json
{
  "user_text": "实时分析摄像头画面",
  "media_input": {
    "source_type": "WEBCAM",
    "camera_config": {
      "camera_id": 0,
      "frame_interval": 2.0,
      "max_duration": 10.0
    }
  },
  "skills_filter": {
    "stage": "cinematographer"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "source_frames": [
      {
        "path": "/path/to/frame1.jpg",
        "index": 0,
        "timestamp_ms": 0
      }
    ],
    "analysis": {
      "subject_visible": true,
      "face_visible": true,
      "tracking_confidence": 0.87,
      "composition_quality": 0.80,
      "summary": "画面构图良好，主体清晰",
      "confidence": 0.85
    },
    "suggestion": {
      "action": "capture_frame",
      "composition": "medium_portrait",
      "reason": "当前构图符合人像拍摄标准"
    },
    "captured_frame": "/path/to/captures/frame_best.jpg",
    "matched_skills": ["skill_003"],
    "skills_guidance": "应用人像构图规则...",
    "user_summary_zh": "已分析当前画面并标记拍摄建议"
  },
  "agent_type": "cinematographer",
  "timestamp": "2026-09-23T10:31:00Z"
}
```

### 3. Editor Agent（编辑智能体）

**端点**: `POST /agents/editor`

**请求体**:
```json
{
  "user_text": "生成人像视频剪辑方案",
  "media_input": {
    "source_type": "FILE",
    "paths": [
      "/path/to/video1.mp4",
      "/path/to/video2.mp4",
      "/path/to/ref_img.jpg"
    ]
  },
  "skills_filter": {
    "stage": "editor"
  },
  "output_config": {
    "output_dir": "/path/to/output",
    "save_intermediate": true
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "timeline": [
      {
        "source": "/path/to/video1.mp4",
        "role": "portrait_source",
        "reason": "主视频素材",
        "keep": true,
        "ai_role": "main_portrait",
        "ai_reason": "主要人物特写"
      }
    ],
    "rendered_preview": "/path/to/output/preview.mp4",
    "render": {
      "ratio": "9:16",
      "format": "mp4"
    },
    "matched_skills": ["skill_004"],
    "skills_guidance": "应用剪辑节奏规则...",
    "analysis_summary": "素材质量良好，适合剪辑",
    "user_summary_zh": "已生成剪辑时间线和预览视频"
  },
  "agent_type": "editor",
  "timestamp": "2026-09-23T10:32:00Z"
}
```

### 4. 完整流程运行

**端点**: `POST /agents/run-all`

**请求体**:
```json
{
  "user_text": "创建一个自然人像视频",
  "media_input": {
    "source_type": "FILE",
    "paths": []
  },
  "media_dir": "/path/to/media",
  "output_config": {
    "output_dir": "/path/to/output"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "skills": [...],
    "director": {...},
    "filming": {...},
    "editing": {...}
  },
  "timestamp": "2026-09-23T10:35:00Z"
}
```

---

## Skills 管理接口

### 1. 列出所有技能

**端点**: `GET /skills`

**查询参数**:
```
?stage=director|cinematographer|editor&limit=10
```

**响应**:
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "skill_001",
        "name": "自然光人像",
        "description": "利用自然光拍摄人像的技巧",
        "stage": "director",
        "tags": ["portrait", "natural_light"],
        "path": "/path/to/skill_001.yaml"
      }
    ],
    "total": 15
  }
}
```

### 2. 获取单个技能详情

**端点**: `GET /skills/{skill_id}`

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "skill_001",
    "name": "自然光人像",
    "description": "利用自然光拍摄人像的技巧",
    "stage": "director",
    "tags": ["portrait", "natural_light"],
    "rules": [
      {
        "rule_id": "rule_001",
        "description": "光线方向规则",
        "content": "自然光应从侧面或前侧照射"
      }
    ],
    "examples": ["example1.jpg"],
    "metadata": {
      "created_at": "2026-09-01T00:00:00Z",
      "updated_at": "2026-09-23T10:00:00Z"
    }
  }
}
```

### 3. 创建新技能

**端点**: `POST /skills`

**请求体**:
```json
{
  "name": "新技能名称",
  "description": "技能描述",
  "stage": "director",
  "tags": ["tag1", "tag2"],
  "rules": [
    {
      "rule_id": "rule_new_001",
      "description": "规则描述",
      "content": "规则内容"
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "skill_new",
    "path": "/path/to/skill_new.yaml",
    "message": "技能创建成功"
  }
}
```

### 4. 更新技能

**端点**: `PUT /skills/{skill_id}`

**请求体**: （同创建接口）

**响应**:
```json
{
  "success": true,
  "data": {
    "id": "skill_001",
    "message": "技能更新成功"
  }
}
```

### 5. 删除技能

**端点**: `DELETE /skills/{skill_id}`

**响应**:
```json
{
  "success": true,
  "data": {
    "message": "技能删除成功"
  }
}
```

### 6. 智能选择技能

**端点**: `POST /skills/select`

**请求体**:
```json
{
  "user_text": "拍摄自然光人像",
  "stage": "director",
  "limit": 3
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "skills": [
      {
        "id": "skill_001",
        "name": "自然光人像",
        "relevance_score": 0.95
      }
    ],
    "total": 3
  }
}
```

---

## WebSocket 实时接口

### 实时摄像头分析

**端点**: `ws://localhost:8765/ws/cinematographer`

**连接建立后发送配置**:
```json
{
  "type": "config",
  "data": {
    "camera_id": 0,
    "user_text": "实时人像拍摄指导",
    "skills_filter": {
      "stage": "cinematographer"
    }
  }
}
```

**服务器响应（初始化成功）**:
```json
{
  "type": "status",
  "message": "摄像头已连接，开始实时分析"
}
```

**服务器推送（分析结果）**:
```json
{
  "type": "analysis",
  "data": {
    "frame_index": 5,
    "timestamp": "2026-09-23T10:30:05Z",
    "analysis": {
      "subject_visible": true,
      "face_visible": true,
      "tracking_confidence": 0.87,
      "composition_quality": 0.80,
      "summary": "画面构图良好"
    },
    "suggestion": {
      "action": "capture_frame",
      "composition": "medium_portrait",
      "reason": "当前构图符合标准"
    },
    "skills_guidance": "保持当前距离和角度"
  }
}
```

**客户端发送停止**:
```json
{
  "type": "stop"
}
```

**服务器响应（停止确认）**:
```json
{
  "type": "status",
  "message": "已停止实时分析"
}
```

---

## 错误处理

### 错误代码

| 代码 | 描述 |
|------|------|
| `VALIDATION_ERROR` | 请求参数验证失败 |
| `FILE_NOT_FOUND` | 文件不存在 |
| `MEDIA_ERROR` | 媒体处理错误 |
| `CAMERA_ERROR` | 摄像头访问错误 |
| `SKILL_NOT_FOUND` | 技能不存在 |
| `API_ERROR` | 外部 API 调用失败 |
| `INTERNAL_ERROR` | 服务器内部错误 |

### 错误响应示例

**文件不存在**:
```json
{
  "success": false,
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "指定的媒体文件不存在",
    "details": {
      "path": "/path/to/missing.mp4"
    }
  },
  "timestamp": "2026-09-23T10:30:00Z"
}
```

**摄像头错误**:
```json
{
  "success": false,
  "error": {
    "code": "CAMERA_ERROR",
    "message": "无法访问摄像头",
    "details": {
      "camera_id": 0,
      "reason": "设备被占用或不存在"
    }
  },
  "timestamp": "2026-09-23T10:30:00Z"
}
```

---

## 前端集成示例

### JavaScript Fetch API 示例

```javascript
// 1. 调用 Director Agent
async function analyzeWithDirector(userText, imagePaths) {
  const response = await fetch('http://localhost:8765/api/v1/agents/director', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_text: userText,
      media_input: {
        source_type: 'FILE',
        paths: imagePaths
      },
      skills_filter: {
        stage: 'director'
      }
    })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('导演方案:', result.data);
  }
}

// 2. WebSocket 实时摄像头分析
function startRealtimeAnalysis() {
  const ws = new WebSocket('ws://localhost:8765/ws/cinematographer');
  
  ws.onopen = () => {
    ws.send(JSON.stringify({
      type: 'config',
      data: {
        camera_id: 0,
        user_text: '实时人像拍摄指导'
      }
    }));
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'analysis') {
      console.log('实时分析:', message.data);
      // 更新 UI 显示分析结果
    }
  };
  
  // 停止分析
  setTimeout(() => {
    ws.send(JSON.stringify({ type: 'stop' }));
  }, 30000);
}
```

---

## 配置说明

### 环境变量

```bash
# API 配置
DASHSCOPE_API_KEY=your_api_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Agent 模型配置
SKILLS_MODEL=qwen-turbo
DIRECTOR_MODEL=qwen-vl-plus
CINEMATOGRAPHER_MODEL=qwen-vl-plus
EDITOR_MODEL=qwen-vl-plus

# 路径配置
MEDIA_DIR=F:/BoldMaker/project00/agents_Module_fast/data
OUTPUT_DIR=F:/BoldMaker/project00/agents_Module_fast/outputs
SKILLS_DIR=F:/BoldMaker/project00/agents_Module_fast/skills/repository
```

### 启动服务

```bash
# 在 D 盘 conda base 环境中运行
cd /d/path/to/agents_Module_fast
python fast.py serve --mode bailian
```

---

## 更新日志

### v1.0 (2026-09-23)
- 初始版本
- 支持本地文件输入
- 支持本地摄像头输入
- 实现四个核心 Agent 接口
- 实现 Skills CRUD 接口
- 实现 WebSocket 实时分析接口

---

**文档结束**
