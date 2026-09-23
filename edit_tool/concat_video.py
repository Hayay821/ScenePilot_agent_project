#!/usr/bin/env python
"""调用火山引擎 MediaKit 的视频拼接工具。

把两个及以上的视频（或图片）URL 提交给 MediaKit 的 concat-video 接口，
接口会返回一个异步任务，本工具会轮询任务直到完成，并给出（或下载）拼接好、
已添加转场的成片。

示例：
    python concat_video.py https://example.com/a.mp4 https://example.com/b.mp4
    python concat_video.py a.mp4 b.jpg --output out.mp4
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import requests

DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")
EXAMPLE_CONFIG_PATH = Path(__file__).with_name("config.example.json")
CREATE_TASK_PATH = "/api/v1/tools/concat-video"
TASK_PATH = "/api/v1/tasks/{task_id}"
SUCCESS_STATUSES = {"completed", "success", "succeeded"}
FAILURE_STATUSES = {"failed", "error", "canceled", "cancelled"}
TERMINAL_STATUSES = SUCCESS_STATUSES | FAILURE_STATUSES


class MediaKitError(RuntimeError):
    """MediaKit 接口返回错误时抛出。"""


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"未找到配置文件 {path}。请复制 config.example.json 为 config.json 并填入 api_key。"
        )
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    api_key = str(config.get("api_key", ""))
    if not api_key or api_key.startswith("YOUR_"):
        raise MediaKitError(f"请在 {path} 中配置有效的 api_key。")
    return config


class MediaKitClient:
    """MediaKit concat-video 的最小客户端。"""

    def __init__(self, config: Dict[str, Any]):
        self.base_url = str(config.get("base_url", "https://mediakit.cn-beijing.volces.com")).rstrip("/")
        self.api_key = config["api_key"]
        self.project = config.get("project", "default")
        self.timeout = float(config.get("timeout_seconds", 60))
        self.poll_interval = float(config.get("poll_interval_seconds", 5))
        self.poll_timeout = float(config.get("poll_timeout_seconds", 600))

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def create_concat_task(
        self,
        video_urls: Iterable[str],
        project: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        urls = [str(url) for url in video_urls]
        if len(urls) < 2:
            raise ValueError("至少需要两个输入素材（视频或图片 URL）。")
        payload: Dict[str, Any] = {"video_urls": urls, "Project": project or self.project}
        if extra:
            payload.update(extra)
        response = requests.post(
            self.base_url + CREATE_TASK_PATH,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        data = self._parse(response)
        task_id = data.get("task_id")
        if not task_id:
            raise MediaKitError(f"创建拼接任务失败，响应缺少 task_id：{data}")
        return str(task_id)

    def get_task(self, task_id: str) -> Dict[str, Any]:
        response = requests.get(
            self.base_url + TASK_PATH.format(task_id=task_id),
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._parse(response)

    def wait_for_task(
        self,
        task_id: str,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        deadline = time.time() + self.poll_timeout
        while True:
            data = self.get_task(task_id)
            status = str(data.get("status", "")).lower()
            if on_progress:
                on_progress(data)
            if status in SUCCESS_STATUSES:
                return data
            if status in FAILURE_STATUSES:
                detail = data.get("message") or data.get("error") or data
                raise MediaKitError(f"任务 {task_id} 失败：{detail}")
            if time.time() > deadline:
                raise TimeoutError(f"任务 {task_id} 超时（{self.poll_timeout:.0f}s）。")
            time.sleep(self.poll_interval)

    @staticmethod
    def _parse(response: requests.Response) -> Dict[str, Any]:
        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            raise MediaKitError(f"服务返回非 JSON 内容：{response.text[:500]}")
        if response.status_code >= 400 or data.get("success") is False:
            raise MediaKitError(f"API 错误（HTTP {response.status_code}）：{data}")
        return data


def concat_videos(
    video_urls: Iterable[str],
    config: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None,
    project: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """提交拼接任务并等待完成，返回任务结果字典（含 result.video_url）。"""
    config = config or load_config(config_path or DEFAULT_CONFIG_PATH)
    client = MediaKitClient(config)
    task_id = client.create_concat_task(video_urls, project=project, extra=extra)
    return client.wait_for_task(task_id, on_progress=on_progress)


def concat_videos_to_url(video_urls: Iterable[str], **kwargs: Any) -> str:
    """便捷封装：直接返回成片 URL。"""
    result = concat_videos(video_urls, **kwargs)
    video_url = (result.get("result") or {}).get("video_url")
    if not video_url:
        raise MediaKitError(f"任务完成但未返回视频地址：{result}")
    return str(video_url)


def download_video(url: str, dest: Path, timeout: float = 600) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with dest.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    handle.write(chunk)
    return dest


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _parse_extra(values: Optional[List[str]]) -> Dict[str, Any]:
    extra: Dict[str, Any] = {}
    for item in values or []:
        key, separator, raw = item.partition("=")
        if not key or not separator:
            raise ValueError(f"参数格式应为 key=value：{item}")
        try:
            extra[key] = json.loads(raw)
        except ValueError:
            extra[key] = raw
    return extra


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="调用火山引擎 MediaKit，将两个及以上视频/图片拼接为一个带转场的视频。"
    )
    parser.add_argument("inputs", nargs="+", help="两个及以上素材 URL（视频或图片）。")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="配置文件路径，默认 edit_tool/config.json")
    parser.add_argument("--project", help="覆盖配置中的 Project。")
    parser.add_argument("--output", help="将结果视频下载到该路径。")
    parser.add_argument("--param", action="append", help="透传额外请求参数，格式 key=value，可多次。")
    parser.add_argument("--quiet", action="store_true", help="不输出轮询进度。")
    args = parser.parse_args(argv)

    for value in args.inputs:
        if not _looks_like_url(value):
            parser.error(
                f"输入必须是可公网访问的 http(s) URL：{value}（云端无法访问本地文件）。"
            )

    try:
        config = load_config(Path(args.config))
        extra = _parse_extra(args.param)

        def progress(data: Dict[str, Any]) -> None:
            if not args.quiet:
                print(f"[{data.get('status')}] task={data.get('task_id')}", file=sys.stderr)

        video_url = concat_videos_to_url(
            args.inputs, config=config, project=args.project, extra=extra, on_progress=progress
        )
        print(video_url)
        if args.output:
            path = download_video(video_url, Path(args.output))
            print(f"已下载到 {path}", file=sys.stderr)
        return 0
    except (MediaKitError, FileNotFoundError, TimeoutError, ValueError) as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
