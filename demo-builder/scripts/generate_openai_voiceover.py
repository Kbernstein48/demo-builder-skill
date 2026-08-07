#!/usr/bin/env python3
"""Generate a cue-timed OpenAI TTS voiceover and mux it onto a rendered video."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "cedar"
DEFAULT_INSTRUCTIONS = (
    "Speak as a calm enterprise product narrator. Use a confident, measured pace. "
    "Keep phrasing clear, avoid theatrical delivery, and leave short pauses between sentences."
)
OVERLAP_TOLERANCE_SECONDS = 0.02


@dataclass(frozen=True)
class Segment:
    index: int
    scene: int
    cue: int
    name: str
    start_seconds: float
    end_seconds: float
    target_audio_seconds: float
    text: str

    @property
    def duration(self) -> float:
        return round(self.end_seconds - self.start_seconds, 3)

    @property
    def label(self) -> str:
        return f"scene {self.scene} cue {self.cue}: {self.name}"

    @property
    def stem(self) -> str:
        return f"{self.index:03d}_scene{self.scene:02d}_cue{self.cue:02d}"


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def ffprobe_duration(path: Path) -> float:
    output = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return float(json.loads(output)["format"]["duration"])


def require_number(raw: Any, field: str, index: int) -> float:
    if isinstance(raw, bool):
        raise SystemExit(f"Segment {index} field {field} must be a number, not boolean.")
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise SystemExit(f"Segment {index} field {field} must be a number.") from None


def default_target_audio(duration: float) -> float:
    margin = min(0.8, max(0.25, duration * 0.12))
    return max(0.1, duration - margin)


def load_segments(path: Path) -> list[Segment]:
    raw_segments = json.loads(path.read_text())
    if not isinstance(raw_segments, list):
        raise SystemExit("Manifest must be a JSON array.")

    segments: list[Segment] = []
    scene_counts: dict[int, int] = {}
    for index, raw in enumerate(raw_segments, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Segment {index} must be a JSON object.")

        try:
            scene = int(raw.get("scene", index))
        except (TypeError, ValueError):
            raise SystemExit(f"Segment {index} field scene must be an integer.") from None

        scene_counts[scene] = scene_counts.get(scene, 0) + 1
        try:
            cue = int(raw.get("cue", raw.get("segment", scene_counts[scene])))
        except (TypeError, ValueError):
            raise SystemExit(f"Segment {index} field cue must be an integer.") from None

        start_seconds = require_number(raw.get("start_seconds"), "start_seconds", index)
        end_seconds = require_number(raw.get("end_seconds"), "end_seconds", index)
        if end_seconds <= start_seconds:
            raise SystemExit(
                f"Segment {index} must end after it starts: "
                f"{start_seconds:.3f}-{end_seconds:.3f}"
            )

        duration = end_seconds - start_seconds
        target_audio_seconds = require_number(
            raw.get("target_audio_seconds", default_target_audio(duration)),
            "target_audio_seconds",
            index,
        )
        if target_audio_seconds <= 0:
            raise SystemExit(f"Segment {index} target_audio_seconds must be positive.")

        name = str(raw.get("name") or raw.get("label") or f"Scene {scene} cue {cue}")
        text = str(raw.get("text", "")).strip()
        segments.append(
            Segment(
                index=index,
                scene=scene,
                cue=cue,
                name=name,
                start_seconds=start_seconds,
                end_seconds=end_seconds,
                target_audio_seconds=target_audio_seconds,
                text=text,
            )
        )

    segments = sorted(segments, key=lambda segment: (segment.start_seconds, segment.index))
    previous: Segment | None = None
    for segment in segments:
        if previous and segment.start_seconds < previous.end_seconds - OVERLAP_TOLERANCE_SECONDS:
            raise SystemExit(
                "Manifest segments overlap: "
                f"{previous.label} ends at {previous.end_seconds:.3f}s, "
                f"{segment.label} starts at {segment.start_seconds:.3f}s."
            )
        previous = segment
    return segments


def require_tool(name: str) -> None:
    try:
        run([name, "-version"], capture=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        raise SystemExit(f"Missing required command: {name}") from None


def load_env_files(extra_paths: list[Path] | None = None) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    script_dir = Path(__file__).resolve().parent
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        script_dir / ".env",
        script_dir.parent / ".env",
    ]
    if extra_paths:
        candidates.extend(extra_paths)
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not resolved.exists():
            continue
        load_dotenv(resolved, override=False)
        seen.add(resolved)


def generate_raw_audio(
    segments: list[Segment],
    raw_dir: Path,
    *,
    model: str,
    voice: str,
    instructions: str,
    overwrite: bool,
) -> None:
    try:
        from openai import OpenAI
    except ImportError:
        raise SystemExit(
            "Missing Python package: openai. Run: python3 -m pip install -r requirements-tts.txt"
        ) from None

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set.")

    client = OpenAI()
    raw_dir.mkdir(parents=True, exist_ok=True)

    for segment in segments:
        if not segment.text:
            print(f"silence cue: {segment.label}")
            continue

        output_path = raw_dir / f"{segment.stem}.wav"
        if output_path.exists() and not overwrite:
            print(f"raw exists: {output_path}")
            continue

        print(f"generating {segment.label}")
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=segment.text,
            instructions=instructions,
            response_format="wav",
        ) as response:
            response.stream_to_file(output_path)


def atempo_filter(speedup: float) -> str:
    factors: list[float] = []
    remaining = speedup
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    factors.append(remaining)
    return ",".join(f"atempo={factor:.6f}" for factor in factors)


def make_silence(path: Path, duration: float) -> Path:
    duration = max(0.001, duration)
    path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=48000:cl=mono",
            "-t",
            f"{duration:.3f}",
            "-c:a",
            "pcm_s16le",
            str(path),
        ]
    )
    return path


def normalize_segment_audio(
    segment: Segment,
    raw_dir: Path,
    padded_dir: Path,
) -> tuple[Path, float | None]:
    target_duration = segment.duration
    padded_path = padded_dir / f"{segment.stem}.wav"

    if not segment.text:
        make_silence(padded_path, target_duration)
        return padded_path, None

    raw_path = raw_dir / f"{segment.stem}.wav"
    if not raw_path.exists():
        raise SystemExit(f"Missing raw audio: {raw_path}")

    raw_duration = ffprobe_duration(raw_path)
    filters = ["aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=mono"]

    max_spoken_duration = max(
        0.1,
        min(segment.target_audio_seconds, max(0.1, target_duration - 0.05)),
    )
    if raw_duration > max_spoken_duration:
        speedup = raw_duration / max_spoken_duration
        filters.append(atempo_filter(speedup))

    filters.append(f"apad=whole_dur={target_duration:.3f}")
    filters.append(f"atrim=0:{target_duration:.3f}")
    filters.append("asetpts=N/SR/TB")

    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(raw_path),
            "-af",
            ",".join(filters),
            str(padded_path),
        ]
    )
    return padded_path, raw_duration


def pad_and_place_audio(
    segments: list[Segment],
    raw_dir: Path,
    padded_dir: Path,
    *,
    video_duration: float,
) -> list[Path]:
    padded_dir.mkdir(parents=True, exist_ok=True)
    padded_paths: list[Path] = []
    cursor = 0.0

    for segment in segments:
        gap = segment.start_seconds - cursor
        if gap > OVERLAP_TOLERANCE_SECONDS:
            gap_path = padded_dir / f"{segment.index:03d}_gap_before.wav"
            make_silence(gap_path, gap)
            padded_paths.append(gap_path)
            print(f"gap before {segment.label}: {gap:.2f}s")
        elif gap < -OVERLAP_TOLERANCE_SECONDS:
            raise SystemExit(
                f"Audio placement overlap before {segment.label}: {gap:.3f}s."
            )

        padded_path, raw_duration = normalize_segment_audio(segment, raw_dir, padded_dir)
        padded_paths.append(padded_path)
        padded_duration = ffprobe_duration(padded_path)
        raw_label = "silence" if raw_duration is None else f"{raw_duration:.2f}s"
        print(
            f"{segment.label}: raw={raw_label} padded={padded_duration:.2f}s "
            f"target={segment.duration:.2f}s"
        )
        cursor = segment.end_seconds

    if cursor > video_duration + OVERLAP_TOLERANCE_SECONDS:
        raise SystemExit(
            f"Manifest ends at {cursor:.2f}s, beyond video duration {video_duration:.2f}s."
        )

    tail = video_duration - cursor
    if tail > OVERLAP_TOLERANCE_SECONDS:
        tail_path = padded_dir / "tail_silence.wav"
        make_silence(tail_path, tail)
        padded_paths.append(tail_path)
        print(f"tail silence: {tail:.2f}s")

    return padded_paths


def concat_audio(paths: list[Path], concat_path: Path, output_path: Path) -> None:
    concat_path.parent.mkdir(parents=True, exist_ok=True)
    concat_path.write_text("".join(f"file '{path.resolve()}'\n" for path in paths))
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            str(output_path),
        ]
    )


def mux_video(video_path: Path, audio_path: Path, output_path: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    )


def dry_run(segments: list[Segment], video_path: Path) -> None:
    video_duration = ffprobe_duration(video_path)
    manifest_duration = segments[-1].end_seconds if segments else 0.0
    print(f"video duration: {video_duration:.2f}s")
    print(f"manifest covered duration: {manifest_duration:.2f}s")

    cursor = 0.0
    for segment in segments:
        gap = segment.start_seconds - cursor
        if gap > OVERLAP_TOLERANCE_SECONDS:
            print(f"gap: {cursor:.2f}-{segment.start_seconds:.2f}s ({gap:.2f}s)")
        print(
            f"{segment.index:03d}. scene={segment.scene} cue={segment.cue} "
            f"{segment.start_seconds:.2f}-{segment.end_seconds:.2f}s "
            f"duration={segment.duration:.2f}s target_audio={segment.target_audio_seconds:.2f}s "
            f"name={segment.name}"
        )
        cursor = segment.end_seconds

    if video_duration - cursor > OVERLAP_TOLERANCE_SECONDS:
        print(f"tail: {cursor:.2f}-{video_duration:.2f}s ({video_duration - cursor:.2f}s)")
    if cursor > video_duration + OVERLAP_TOLERANCE_SECONDS:
        print(
            f"warning: manifest ends at {cursor:.2f}s, beyond video duration {video_duration:.2f}s"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("voiceover_segments.json"))
    parser.add_argument("--video", type=Path, default=Path("final.mp4"))
    parser.add_argument("--out-dir", type=Path, default=Path("narration/openai"))
    parser.add_argument("--output", type=Path, default=Path("final_narrated.mp4"))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--voice")
    parser.add_argument(
        "--instructions",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env_candidates = [
        args.manifest.parent / ".env",
        args.video.parent / ".env",
        args.output.parent / ".env",
    ]
    if args.env_file:
        env_candidates.insert(0, args.env_file)
    load_env_files(env_candidates)

    args.model = args.model or os.environ.get("OPENAI_TTS_MODEL", DEFAULT_MODEL)
    args.voice = args.voice or os.environ.get("OPENAI_TTS_VOICE", DEFAULT_VOICE)
    args.instructions = args.instructions or os.environ.get(
        "OPENAI_TTS_INSTRUCTIONS", DEFAULT_INSTRUCTIONS
    )

    require_tool("ffmpeg")
    require_tool("ffprobe")

    segments = load_segments(args.manifest)
    if not args.video.exists():
        raise SystemExit(f"Missing video: {args.video}")

    if args.dry_run:
        dry_run(segments, args.video)
        return 0

    raw_dir = args.out_dir / "raw"
    padded_dir = args.out_dir / "padded"
    voiceover_path = args.out_dir / "voiceover.wav"
    concat_path = args.out_dir / "audio_concat.txt"
    video_duration = ffprobe_duration(args.video)

    generate_raw_audio(
        segments,
        raw_dir,
        model=args.model,
        voice=args.voice,
        instructions=args.instructions,
        overwrite=args.overwrite,
    )
    padded_paths = pad_and_place_audio(
        segments,
        raw_dir,
        padded_dir,
        video_duration=video_duration,
    )
    concat_audio(padded_paths, concat_path, voiceover_path)
    mux_video(args.video, voiceover_path, args.output)

    output_duration = ffprobe_duration(args.output)
    audio_duration = ffprobe_duration(voiceover_path)
    print(f"voiceover: {voiceover_path} ({audio_duration:.2f}s)")
    print(f"muxed video: {args.output} ({output_duration:.2f}s, source {video_duration:.2f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
