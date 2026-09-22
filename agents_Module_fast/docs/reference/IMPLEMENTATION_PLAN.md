# ScenePilot Fast Implementation Plan

## Goal

This directory is the overnight, lightweight prototype. It proves the core media workflow before any camera SDK or platform work:

```text
local image/video
  -> frame extraction
  -> SkillsManager selects local English skills
  -> Director returns a shot plan
  -> Cinematographer analyzes frames and suggests capture_frame/wait
  -> Editor creates a timeline and exports preview.mp4
```

## Four agents

| Agent | Input | Output | Current implementation |
|---|---|---|---|
| SkillsManager | Chinese user text, stage, expert rules | selected English skills, Chinese explanation, local draft | `SkillManager`, `SkillsManagerAgent` |
| Director | user text, optional reference images, director skills | shot plan | `DirectorAgent` |
| Cinematographer | images or extracted video frames, cinematographer skills | visual analysis and capture suggestion | `CinematographerAgent` |
| Editor | local videos/images, editor skills | timeline and `preview.mp4` | `EditorAgent` |

The four logical agents are implemented in one small module on purpose. This is not a production framework.

## Input/output contract

Input directories:

```text
data/
  img/       input images: jpg/jpeg/png/webp
  video/     input videos: mp4/mov/avi/mkv/insv
```

Output directory:

```text
outputs/
  frames/
  preview.mp4
  run.json
```

Future modules can call the same Python functions or HTTP endpoints:

```text
POST /skills/interact
POST /director
POST /cinematographer
POST /editor
POST /run
GET  /health
```

## Models

`mock` is the default and is required for tests. `bailian` uses the OpenAI-compatible DashScope endpoint configured by:

```text
DASHSCOPE_API_KEY
DASHSCOPE_BASE_URL
DASHSCOPE_MODEL
```

No model training is required. No video is sent as a whole to the model. Videos are sampled into local frames first.

## Skills

All Skill files are English YAML to avoid encoding-sensitive identifiers. User conversation and explanations can remain Chinese.

```text
skills/repository/builtin/director/*.yaml
skills/repository/builtin/cinematographer/*.yaml
skills/repository/builtin/editor/*.yaml
```

Expert authoring writes a local `draft` YAML. There is no cloud Skill feature in this prototype.

## Do not expand tonight

- No database, Redis, Kafka, or event bus.
- No separate Agent base-class hierarchy.
- No camera SDK.
- No real-time camera control.
- No web frontend.
- No cloud Skill repository.
- No multi-agent conversation graph.
- No large test tree.

## Acceptance

```bash
pytest -q
python fast.py skills --text "我想拍自然的人像短片"
python fast.py run --mode mock --text "我想拍自然的人像短片" --media media
```

With a real video in `media/`, acceptance requires:

- extracted JPG frames;
- Director JSON shot plan;
- Cinematographer JSON visual suggestion;
- Editor timeline JSON;
- playable `outputs/preview.mp4`.
