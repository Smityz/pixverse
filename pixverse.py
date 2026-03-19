"""Minimal Pixverse SDK — text-to-video only."""

import time
import uuid
from enum import IntEnum

import httpx

BASE_URL = "https://app-api.pixverse.ai"


class VideoStatus(IntEnum):
    SUCCESS = 1
    GENERATING = 5
    CONTENT_BLOCKED = 7
    FAILED = 8


class PixverseError(Exception):
    def __init__(self, code: int, msg: str):
        super().__init__(f"[{code}] {msg}")
        self.code = code


class PixverseClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL, timeout: int = 30):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _headers(self) -> dict:
        return {
            "API-KEY": self._api_key,
            "Ai-trace-id": str(uuid.uuid4()),
            "Content-Type": "application/json",
        }

    def _check(self, data: dict) -> dict:
        if data.get("ErrCode", -1) != 0:
            raise PixverseError(data["ErrCode"], data.get("ErrMsg", "unknown error"))
        return data["Resp"]

    def generate(
        self,
        prompt: str,
        *,
        model: str = "v4.5",
        aspect_ratio: str = "16:9",
        duration: int = 5,
        quality: str = "540p",
        negative_prompt: str = "",
        motion_mode: str = "normal",
        camera_movement: str | None = None,
        style: str | None = None,
        seed: int | None = None,
    ) -> int:
        """Submit a text-to-video job. Returns video_id."""
        payload: dict = {
            "prompt": prompt,
            "model": model,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "quality": quality,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if motion_mode != "normal":
            payload["motion_mode"] = motion_mode
        if camera_movement:
            payload["camera_movement"] = camera_movement
        if style:
            payload["style"] = style
        if seed is not None:
            payload["seed"] = seed

        resp = httpx.post(
            f"{self._base_url}/openapi/v2/video/text/generate",
            headers=self._headers(),
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return self._check(resp.json())["video_id"]

    def status(self, video_id: int) -> dict:
        """Poll video status. Returns the Resp dict."""
        resp = httpx.get(
            f"{self._base_url}/openapi/v2/video/result/{video_id}",
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return self._check(resp.json())

    def wait(
        self,
        video_id: int,
        poll_interval: float = 5.0,
        timeout: float = 600.0,
    ) -> str:
        """Block until video is ready. Returns the download URL."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = self.status(video_id)
            s = result["status"]
            if s == VideoStatus.SUCCESS:
                return result["url"]
            if s == VideoStatus.GENERATING:
                time.sleep(poll_interval)
                continue
            if s == VideoStatus.CONTENT_BLOCKED:
                raise PixverseError(s, "content blocked by moderation")
            raise PixverseError(s, f"generation failed (status={s})")
        raise TimeoutError(f"video {video_id} not ready after {timeout}s")
