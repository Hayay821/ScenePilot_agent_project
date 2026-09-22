"""ScenePilot Fast: a small, media-first four-agent prototype.

The module intentionally keeps the runtime surface small. Skills are English YAML,
user interaction can be Chinese, and every agent returns JSON-serializable data.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import cv2
from dotenv import load_dotenv

from agents.skills_manager_agent import SkillManager, SkillsManagerAgent
from agents.director_agent import DirectorAgent
from agents.cinematographer_agent import CinematographerAgent
from agents.editor_agent import EditorAgent

ROOT = Path(__file__).resolve().parent
SKILLS_DIR = ROOT / "skills" / "repository"
MEDIA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"

# Load .env file
load_dotenv(ROOT / ".env")


def _json(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json(v) for v in value]
    return value


class MediaTools:
    """Small local image/video adapter. No camera SDK is required."""

    @staticmethod
    def images(directory: str | Path) -> list[str]:
        root = Path(directory)
        return [str(p) for p in sorted(root.glob("**/*")) if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]

    @staticmethod
    def videos(directory: str | Path) -> list[str]:
        root = Path(directory)
        return [str(p) for p in sorted(root.glob("**/*")) if p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".insv"}]

    @staticmethod
    def extract_frames(video: str | Path, output: str | Path, every_seconds: float = 2.0, max_frames: int = 12) -> list[str]:
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        step = max(1, int(fps * every_seconds))
        paths, index = [], 0
        while len(paths) < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if index % step == 0:
                path = output / f"frame_{index:06d}.jpg"
                cv2.imwrite(str(path), frame)
                paths.append(str(path))
            index += 1
        cap.release()
        return paths

    @staticmethod
    def inspect(path: str | Path) -> dict:
        path = Path(path)
        if path.is_dir():
            return {"path": str(path), "type": "directory", "images": MediaTools.images(path), "videos": MediaTools.videos(path)}
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            image = cv2.imread(str(path))
            height, width = image.shape[:2]
            return {"path": str(path), "type": "image", "width": width, "height": height}
        cap = cv2.VideoCapture(str(path))
        result = {"path": str(path), "type": "video", "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), "fps": cap.get(cv2.CAP_PROP_FPS), "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))}
        cap.release()
        return result

    @staticmethod
    def rough_cut(video: str | Path, output: str | Path, start: float = 0, duration: float = 10) -> str:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", str(video), "-t", str(duration), "-c", "copy", str(output)], check=True, capture_output=True)
        return str(output)


class Provider:
    """Vision provider supporting both mock and real Bailian Qwen-VL API."""

    def __init__(self, mode: str = "mock", model: str | None = None, agent_type: str | None = None):
        self.mode = mode
        # Support both DASHSCOPE_ and BAILIAN_ prefixes, also check API_KEY
        self.api_key = (
            os.getenv("DASHSCOPE_API_KEY") or
            os.getenv("BAILIAN_API_KEY") or
            os.getenv("API_KEY")
        )
        # Strip whitespace to prevent HTTP header errors
        if self.api_key:
            self.api_key = self.api_key.strip()
        self.base_url = (
            os.getenv("DASHSCOPE_BASE_URL") or
            os.getenv("BAILIAN_BASE_URL") or
            os.getenv("API_URL") or
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # Select model based on agent type if not explicitly provided
        if model:
            self.model = model
        elif agent_type:
            # Agent-specific model selection
            agent_model_map = {
                "skills": os.getenv("SKILLS_MODEL") or "qwen-turbo",
                "director": os.getenv("DIRECTOR_MODEL") or "qwen-vl-plus",
                "cinematographer": os.getenv("CINEMATOGRAPHER_MODEL") or "qwen-vl-plus",
                "editor": os.getenv("EDITOR_MODEL") or "qwen-vl-plus",
            }
            self.model = agent_model_map.get(agent_type)

        # Fallback to default model
        if not self.model:
            self.model = (
                os.getenv("DASHSCOPE_MODEL") or
                os.getenv("BAILIAN_MODEL") or
                os.getenv("MODEL") or
                "qwen-vl-plus"
            )

        if self.mode == "bailian" and not self.api_key:
            raise ValueError(
                "Bailian mode requires API key. Please set DASHSCOPE_API_KEY, "
                "BAILIAN_API_KEY, or API_KEY in .env file or environment."
            )

    def text(self, prompt: str, expect_json: bool = False) -> dict:
        """Call text-only model (for skills manager).

        Args:
            prompt: Text prompt for the model
            expect_json: Whether to expect JSON response

        Returns:
            Dictionary with analysis results
        """
        if self.mode == "mock":
            return {
                "summary": "Mock text analysis",
                "confidence": 0.75
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # Call API with text only
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            result_text = response.choices[0].message.content

            # Try to extract JSON if expected
            if expect_json:
                return self._extract_json(result_text)

            return {
                "summary": result_text,
                "confidence": 0.8
            }

        except Exception as e:
            error_msg = str(e)
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                raise ValueError(f"API authentication failed. Please check DASHSCOPE_API_KEY in .env: {error_msg}")
            elif "model" in error_msg.lower():
                raise ValueError(f"Model '{self.model}' not available. Please check model configuration in .env: {error_msg}")
            else:
                raise ValueError(f"Text API call failed: {error_msg}")

    def vision(self, prompt: str, media: list[str], expect_json: bool = False) -> dict:
        """Call vision model with images.

        Args:
            prompt: Text prompt for the model
            media: List of image paths (max 6 will be used)
            expect_json: Whether to expect JSON response

        Returns:
            Dictionary with analysis results
        """
        if self.mode == "mock":
            return {
                "summary": "Mock analysis: a person is visible; keep the subject clear and leave directional space.",
                "events": ["subject_visible"],
                "confidence": 0.75
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            # Build content with text and images
            content = [{"type": "text", "text": prompt}]
            for path in media[:6]:  # Limit to 6 images
                encoded = base64.b64encode(Path(path).read_bytes()).decode()
                mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{encoded}"}
                })

            # Call API
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                temperature=0.2
            )

            result_text = response.choices[0].message.content

            # Try to extract JSON if expected
            if expect_json:
                return self._extract_json(result_text)

            return {
                "summary": result_text,
                "events": [],
                "confidence": 0.8
            }

        except Exception as e:
            error_msg = str(e)
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                raise ValueError(f"API authentication failed. Please check DASHSCOPE_API_KEY in .env: {error_msg}")
            elif "model" in error_msg.lower():
                raise ValueError(f"Model '{self.model}' not available. Please check DASHSCOPE_MODEL in .env: {error_msg}")
            else:
                raise ValueError(f"Vision API call failed: {error_msg}")

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON from text, handling markdown code fences."""
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code fence
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        # Return wrapped text if no JSON found
        return {"summary": text, "confidence": 0.5, "parse_error": True}


class ScenePilotFast:
    def __init__(self, mode: str = "mock", skills_root: Path | None = None):
        skills_root = skills_root or SKILLS_DIR
        self.skills = SkillManager(skills_root)

        # Create separate providers for each agent with their specific models
        self.skills_provider = Provider(mode, agent_type="skills")
        self.director_provider = Provider(mode, agent_type="director")
        self.cinematographer_provider = Provider(mode, agent_type="cinematographer")
        self.editor_provider = Provider(mode, agent_type="editor")

        # Initialize agents with their dedicated providers
        self.manager = SkillsManagerAgent(self.skills, self.skills_provider)
        self.director = DirectorAgent(self.director_provider)
        self.cinematographer = CinematographerAgent(self.cinematographer_provider)
        self.editor = EditorAgent(self.editor_provider)

    def run_all(self, user_text: str, media_dir: str | None = None) -> dict:
        media_dir = media_dir or str(MEDIA_DIR)
        images, videos = MediaTools.images(media_dir), MediaTools.videos(media_dir)

        # Select skills
        selected = self.skills.select(user_text)
        if not selected:
            selected = self.skills.list()[:3]

        # Run Director
        director_skills = [s for s in selected if s.get("stage") == "director"] or selected[:1]
        director_result = self.director.run(user_text, director_skills, images[:6])

        # Save director output
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "director.json").write_text(
            json.dumps(_json(director_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Run Cinematographer
        frames = []
        if videos:
            video_name = Path(videos[0]).stem
            frames_dir = OUTPUT_DIR / "frames" / video_name
            frames = MediaTools.extract_frames(videos[0], frames_dir)

        cinematographer_skills = [s for s in selected if s.get("stage") == "cinematographer"] or selected[:1]
        filming_result = self.cinematographer.run(
            frames or images[:3],
            cinematographer_skills,
            user_text
        )

        # Save filming output
        (OUTPUT_DIR / "filming.json").write_text(
            json.dumps(_json(filming_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Run Editor
        editor_skills = [s for s in selected if s.get("stage") == "editor"] or selected[:1]
        editing_result = self.editor.run(videos, images, editor_skills, OUTPUT_DIR)

        # Save editing output
        (OUTPUT_DIR / "edit_plan.json").write_text(
            json.dumps(_json(editing_result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Compile full result
        result = {
            "skills": selected,
            "director": director_result,
            "filming": filming_result,
            "editing": editing_result
        }

        # Save combined run.json
        (OUTPUT_DIR / "run.json").write_text(
            json.dumps(_json(result), ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return result


def build_api(app: ScenePilotFast):
    from fastapi import FastAPI
    from pydantic import BaseModel
    api = FastAPI(title="ScenePilot Fast")

    class TextRequest(BaseModel):
        text: str
        stage: str = "director"

    class MediaRequest(BaseModel):
        text: str = ""
        images: list[str] = []
        frames: list[str] = []
        videos: list[str] = []

    @api.get("/health")
    def health(): return {"ok": True}

    @api.post("/skills/interact")
    def skills_interact(req: TextRequest): return app.manager.interact(req.text, req.stage)

    @api.post("/director")
    def director(req: MediaRequest):
        skills = app.skills.select(req.text, "director")
        return app.director.run(req.text, skills, req.images)

    @api.post("/cinematographer")
    def cinematographer(req: MediaRequest):
        skills = app.skills.select(req.text, "cinematographer")
        return app.cinematographer.run(req.frames or req.images, skills, req.text)

    @api.post("/editor")
    def editor(req: MediaRequest):
        skills = app.skills.select(req.text, "editor")
        return app.editor.run(req.videos, req.images, skills, OUTPUT_DIR)

    @api.post("/run")
    def run(req: TextRequest): return app.run_all(req.text)

    return api


def main() -> None:
    parser = argparse.ArgumentParser(description="ScenePilot Fast")
    parser.add_argument("command", choices=["run", "skills", "frames", "inspect", "serve"])
    parser.add_argument("--text", default="Create a natural portrait video")
    parser.add_argument("--media", default=str(MEDIA_DIR))
    parser.add_argument("--video")
    parser.add_argument("--mode", choices=["mock", "bailian"], default="mock")
    args = parser.parse_args()
    app = ScenePilotFast(args.mode)
    if args.command == "skills": print(json.dumps(app.manager.interact(args.text, "director"), ensure_ascii=False, indent=2))
    elif args.command == "run": print(json.dumps(_json(app.run_all(args.text, args.media)), ensure_ascii=False, indent=2))
    elif args.command == "inspect": print(json.dumps(MediaTools.inspect(args.media), ensure_ascii=False, indent=2))
    elif args.command == "frames": print(json.dumps(MediaTools.extract_frames(args.video, OUTPUT_DIR / "frames"), ensure_ascii=False, indent=2))
    elif args.command == "serve":
        import uvicorn
        uvicorn.run(build_api(app), host="127.0.0.1", port=8765)


if __name__ == "__main__": main()
