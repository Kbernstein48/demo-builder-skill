"""Frame-locked Manim cue clock with opt-in storyboard capture."""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

from manim import config, linear
from PIL import Image


ROOT = Path(__file__).resolve().parent
TIMELINE_PATH = Path(os.environ.get("DEMO_TIMELINE_PATH", ROOT / "timeline.json")).expanduser().resolve()
TIMELINE = json.loads(TIMELINE_PATH.read_text())
FPS = int(TIMELINE["fps"])
SCENES = {scene["id"]: scene for scene in TIMELINE["scenes"]}


class CueClock:
    """Drive scene animation from named cue markers and fail on timing drift."""

    def __init__(self, scene: Any, scene_id: str) -> None:
        self.scene = scene
        self.scene_id = scene_id
        self.spec = SCENES[scene_id]
        self.cues = {cue["id"]: cue for cue in self.spec["cues"]}
        self.events: list[dict[str, Any]] = []
        self.cues_with_motion: set[str] = set()
        self.tolerance_frames = max(1, math.ceil(FPS / float(config.frame_rate)))
        capture_root = os.environ.get("STORYBOARD_CAPTURE_DIR")
        event_root = os.environ.get("STORYBOARD_EVENT_CAPTURE_DIR")
        sync_root = os.environ.get("STORYBOARD_SYNC_DIR")
        self.capture_dir = Path(capture_root).expanduser().resolve() if capture_root else None
        self.event_capture_dir = Path(event_root).expanduser().resolve() if event_root else None
        self.sync_dir = Path(sync_root).expanduser().resolve() if sync_root else ROOT / "sync-events"
        self.capture_index = 0

    def frame(self) -> int:
        return round(float(self.scene.time) * FPS)

    def marker(self, cue_id: str, marker: str) -> int:
        return int(self.cues[cue_id]["markers"][marker])

    def seek_frame(self, expected: int, *, reason: str) -> None:
        actual = self.frame()
        if actual > expected + self.tolerance_frames:
            raise RuntimeError(
                f"{self.scene_id} late for {reason}: expected frame {expected}, actual {actual}"
            )
        if actual < expected:
            self.scene.wait((expected - actual) / FPS)

    def seek(self, cue_id: str, marker: str) -> None:
        self.seek_frame(self.marker(cue_id, marker), reason=f"{cue_id}.{marker}")

    def play(
        self,
        cue_id: str,
        start_marker: str,
        end_marker: str,
        *animations: Any,
        rate_func=linear,
        event: str | None = None,
    ) -> None:
        start = self.marker(cue_id, start_marker)
        end = self.marker(cue_id, end_marker)
        if end <= start:
            raise RuntimeError(f"Invalid marker interval {cue_id}: {start_marker}->{end_marker}")
        self.seek_frame(start, reason=f"{cue_id}.{start_marker}")
        actual_start = self.frame()
        self.capture_event(cue_id, start_marker, actual_start)
        remaining = end - actual_start
        if remaining <= 0:
            raise RuntimeError(f"No time remains for {self.scene_id}/{cue_id}")
        self.scene.play(*animations, run_time=remaining / FPS, rate_func=rate_func)
        actual_end = self.frame()
        self.capture_event(cue_id, end_marker, actual_end)
        if abs(actual_end - end) > self.tolerance_frames:
            raise RuntimeError(
                f"{self.scene_id} drift in {cue_id}: expected end {end}, actual {actual_end}"
            )
        self.cues_with_motion.add(cue_id)
        self.events.append(
            {
                "cue_id": cue_id,
                "visual_event_id": self.cues[cue_id].get("visual_event_id", cue_id),
                "event": event or self.cues[cue_id].get("visual_event_id", cue_id),
                "expected_start_frame": start,
                "actual_start_frame": actual_start,
                "expected_end_frame": end,
                "actual_end_frame": actual_end,
            }
        )

    def finish_cue(self, cue_id: str) -> None:
        if cue_id not in self.cues_with_motion:
            raise RuntimeError(f"Spoken cue has no visual event: {self.scene_id}/{cue_id}")
        self.seek(cue_id, "settle")
        self.capture_settle(cue_id)

    def capture_settle(self, cue_id: str) -> None:
        if self.capture_dir is None:
            return
        scene_dir = self.capture_dir / self.scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", cue_id)
        self._save_current_frame(scene_dir / f"{self.capture_index:02d}-{safe_id}-settle.png")
        self.capture_index += 1

    def capture_event(self, cue_id: str, marker: str, frame_number: int) -> None:
        if self.event_capture_dir is None:
            return
        scene_dir = self.event_capture_dir / self.scene_id
        scene_dir.mkdir(parents=True, exist_ok=True)
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "-", cue_id)
        self._save_current_frame(scene_dir / f"{safe_id}--{frame_number:05d}--{marker}.png")

    def _save_current_frame(self, output: Path) -> None:
        self.scene.renderer.static_image = None
        self.scene.renderer.update_frame(self.scene, ignore_skipping=True)
        Image.fromarray(self.scene.renderer.get_frame()).save(output)

    def finish_scene(self) -> None:
        missing = [cue_id for cue_id in self.cues if cue_id not in self.cues_with_motion]
        if missing:
            raise RuntimeError(f"{self.scene_id} cues without motion: {missing}")
        expected = int(self.spec["duration_frames"])
        self.seek_frame(expected, reason="scene.end")
        actual = self.frame()
        if abs(actual - expected) > self.tolerance_frames:
            raise RuntimeError(
                f"{self.scene_id} duration drift: expected {expected}, actual {actual}"
            )
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "scene_id": self.scene_id,
            "fps": FPS,
            "expected_duration_frames": expected,
            "actual_duration_frames": actual,
            "events": self.events,
        }
        (self.sync_dir / f"{self.scene_id}.json").write_text(json.dumps(payload, indent=2) + "\n")

