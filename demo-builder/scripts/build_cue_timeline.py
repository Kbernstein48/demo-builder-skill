#!/usr/bin/env python3
"""Compile frame-quantized demo timing from voiceover_cues.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import wave
from pathlib import Path


def normalize(text: str) -> str:
    return " ".join(text.split())


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


def parse_script_scenes(path: Path) -> list[str]:
    if not path.exists():
        return []
    source = path.read_text()
    matches = re.findall(
        r"^## Scene[^\n]*\n\n(.*?)(?=^## Scene|\Z)",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    return [normalize(match) for match in matches]


def wav_info(path: Path) -> tuple[int, int, float]:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
        return frames, rate, frames / rate


def estimate_seconds(text: str, words_per_minute: float) -> float:
    words_per_second = words_per_minute / 60.0
    punctuation = 0.10 * text.count(",") + 0.16 * sum(text.count(mark) for mark in ".;:?")
    return max(1.20, word_count(text) / words_per_second + punctuation)


def relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def build(args: argparse.Namespace) -> tuple[dict, list[dict], list[dict]]:
    spec = json.loads(args.cues.read_text())
    fps = int(spec.get("fps", args.fps))
    scenes = spec.get("scenes", [])
    if not scenes:
        raise SystemExit(f"No scenes found in {args.cues}")

    scripted = parse_script_scenes(args.script)
    if scripted:
        if len(scripted) != len(scenes):
            raise SystemExit(f"Narration scenes={len(scripted)} but cue scenes={len(scenes)}")
        for scene, script_text in zip(scenes, scripted):
            cue_text = normalize(" ".join(cue["text"] for cue in scene["cues"]))
            if cue_text != script_text:
                raise SystemExit(f"Narration drift in {scene['id']}")

    timeline = {
        "fps": fps,
        "mode": "audio_locked" if args.from_raw else "estimated",
        "scenes": [],
    }
    manifest: list[dict] = []
    audio_lock: list[dict] = []
    global_frame = 0
    linear_index = 0

    for scene_number, scene in enumerate(scenes, start=1):
        local_frame = 0
        compiled_cues: list[dict] = []
        cue_specs = scene.get("cues", [])
        if not cue_specs:
            raise SystemExit(f"Scene has no cues: {scene['id']}")

        for cue_number, cue in enumerate(cue_specs, start=1):
            linear_index += 1
            default_name = f"{linear_index:03d}_scene{scene_number:02d}_cue{cue_number:02d}.wav"
            raw_path = args.raw_dir / cue.get("audio_file", default_name)
            if args.from_raw:
                if not raw_path.exists():
                    raise SystemExit(f"Missing raw narration cue: {raw_path}")
                sample_count, sample_rate, audio_seconds = wav_info(raw_path)
            else:
                sample_rate = args.sample_rate
                audio_seconds = estimate_seconds(cue["text"], args.wpm)
                sample_count = round(audio_seconds * sample_rate)

            pre_frames = args.pre_frames
            post_frames = args.last_post_frames if cue_number == len(cue_specs) else args.post_frames
            audio_frames = math.ceil(audio_seconds * fps)
            minimum_frames = math.ceil(args.min_cue_seconds * fps)
            cue_frames = max(minimum_frames, pre_frames + audio_frames + post_frames)
            start_frame = local_frame
            end_frame = start_frame + cue_frames
            audio_start_frame = start_frame + pre_frames
            audio_end_frame = min(end_frame - post_frames, audio_start_frame + audio_frames)
            focus_frame = audio_start_frame + max(
                1,
                round((audio_end_frame - audio_start_frame) * args.focus_ratio),
            )

            compiled = {
                "id": cue["id"],
                "name": cue.get("name", cue["id"]),
                "text": cue["text"],
                "visual_event_id": cue.get("visual_event_id", cue["id"]),
                "start_frame": start_frame,
                "end_frame": end_frame,
                "duration_frames": cue_frames,
                "markers": {
                    "start": start_frame,
                    "onset": audio_start_frame,
                    "focus": focus_frame,
                    "land": audio_end_frame,
                    "settle": end_frame,
                },
                "raw_audio_seconds": round(audio_seconds, 6),
            }
            compiled_cues.append(compiled)

            absolute_audio_start = (global_frame + audio_start_frame) / fps
            absolute_audio_end = (global_frame + audio_end_frame) / fps
            item = {
                "scene": scene_number,
                "cue": cue_number,
                "name": f"{scene['id']}:{compiled['name']}",
                "start_seconds": round(absolute_audio_start, 3),
                "end_seconds": round(absolute_audio_end, 3),
                "target_audio_seconds": round(audio_seconds, 3),
                "speaker": cue.get("speaker", "Narrator"),
                "voice_style": cue.get("voice_style", spec.get("voice_style", "")),
                "visual_event_id": compiled["visual_event_id"],
                "text": cue["text"],
            }
            for field in (
                "elevenlabs_voice_id",
                "elevenlabs_voice_name",
                "voice_name",
                "elevenlabs_model",
                "tts_speed",
            ):
                value = cue.get(field, spec.get(field))
                if value is not None:
                    item[field] = value
            if "voice" in spec and "elevenlabs_voice_name" not in item and "voice_name" not in item:
                item["elevenlabs_voice_name"] = spec["voice"]
            if "model" in spec and "elevenlabs_model" not in item:
                item["elevenlabs_model"] = spec["model"]
            manifest.append(item)

            audio_lock.append(
                {
                    "index": linear_index,
                    "scene": scene_number,
                    "cue": cue_number,
                    "cue_id": cue["id"],
                    "text_sha256": hashlib.sha256(cue["text"].encode()).hexdigest(),
                    "audio_file": relative_or_absolute(raw_path, args.output_dir),
                    "sample_count": sample_count,
                    "sample_rate": sample_rate,
                    "duration_seconds": round(audio_seconds, 6),
                    "measured": args.from_raw,
                }
            )
            local_frame = end_frame

        timeline["scenes"].append(
            {
                "id": scene["id"],
                "title": scene.get("title", scene["id"]),
                "global_start_frame": global_frame,
                "duration_frames": local_frame,
                "duration_seconds": round(local_frame / fps, 6),
                "cues": compiled_cues,
            }
        )
        global_frame += local_frame

    timeline["duration_frames"] = global_frame
    timeline["duration_seconds"] = round(global_frame / fps, 6)
    return timeline, manifest, audio_lock


def write_report(path: Path, timeline: dict, manifest: list[dict]) -> None:
    lines = [
        "# Cue synchronization report",
        "",
        f"- Mode: `{timeline['mode']}`",
        f"- Frame rate: {timeline['fps']} fps",
        f"- Scenes: {len(timeline['scenes'])}",
        f"- Spoken cues: {len(manifest)}",
        f"- Total duration: {timeline['duration_seconds']:.3f} seconds",
        "- Every cue has a visual event ID: yes",
        "",
        "| Scene | Cues | Duration | Longest cue |",
        "|---|---:|---:|---:|",
    ]
    for scene in timeline["scenes"]:
        longest = max(cue["duration_frames"] for cue in scene["cues"]) / timeline["fps"]
        lines.append(
            f"| {scene['id']} | {len(scene['cues'])} | "
            f"{scene['duration_seconds']:.2f}s | {longest:.2f}s |"
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cues", type=Path, default=Path("voiceover_cues.json"))
    parser.add_argument("--script", type=Path, default=Path("voiceover_script.md"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--raw-dir", type=Path, default=Path("narration/raw"))
    parser.add_argument("--from-raw", action="store_true")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--wpm", type=float, default=144.0)
    parser.add_argument("--sample-rate", type=int, default=48000)
    parser.add_argument("--pre-frames", type=int, default=6)
    parser.add_argument("--post-frames", type=int, default=12)
    parser.add_argument("--last-post-frames", type=int, default=48)
    parser.add_argument("--min-cue-seconds", type=float, default=2.2)
    parser.add_argument("--focus-ratio", type=float, default=0.42)
    args = parser.parse_args()

    args.cues = args.cues.resolve()
    args.script = args.script.resolve()
    args.output_dir = args.output_dir.resolve()
    args.raw_dir = args.raw_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    timeline, manifest, audio_lock = build(args)
    (args.output_dir / "timeline.json").write_text(json.dumps(timeline, indent=2) + "\n")
    (args.output_dir / "voiceover_segments.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (args.output_dir / "audio_lock.json").write_text(json.dumps(audio_lock, indent=2) + "\n")
    write_report(args.output_dir / "sync_report.md", timeline, manifest)
    print(
        f"wrote timeline.json, voiceover_segments.json, audio_lock.json; "
        f"duration={timeline['duration_seconds']:.3f}s cues={len(manifest)} mode={timeline['mode']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

