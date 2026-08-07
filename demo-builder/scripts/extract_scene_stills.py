#!/usr/bin/env python3
"""Extract review key frames from a Manim concat list and create a contact sheet."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else ""


def ffprobe_json(path: Path, entries: str) -> dict:
    raw = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            entries,
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(raw)


def ffprobe_duration(path: Path) -> float:
    return float(ffprobe_json(path, "format=duration")["format"]["duration"])


def ffprobe_dimensions(path: Path) -> tuple[int, int]:
    info = ffprobe_json(path, "stream=width,height")
    stream = info["streams"][0]
    return int(stream["width"]), int(stream["height"])


def parse_concat(concat_path: Path) -> list[Path]:
    base = concat_path.parent
    paths: list[Path] = []
    for line in concat_path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("file "):
            continue
        value = line[5:].strip()
        if value[0] in {"'", '"'} and value[-1] == value[0]:
            value = value[1:-1]
        path = Path(value)
        paths.append(path if path.is_absolute() else base / path)
    return paths


def sample_timestamps(duration: float, samples_per_scene: int, offset: float) -> list[float]:
    if samples_per_scene <= 1:
        return [max(0.0, duration - offset)]

    last = max(0.0, duration - offset)
    if samples_per_scene == 2:
        return [max(0.0, duration * 0.35), last]

    middle_count = samples_per_scene - 1
    middle = [
        duration * fraction / (middle_count + 1)
        for fraction in range(1, middle_count + 1)
    ]
    return [min(max(0.0, timestamp), last) for timestamp in middle] + [last]


def extract_stills(
    paths: list[Path],
    out_dir: Path,
    offset: float,
    samples_per_scene: int,
) -> tuple[list[Path], list[dict]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stills: list[Path] = []
    manifest: list[dict] = []
    for index, path in enumerate(paths, start=1):
        if not path.exists():
            raise SystemExit(f"Missing scene video: {path}")
        duration = ffprobe_duration(path)
        timestamps = sample_timestamps(duration, samples_per_scene, offset)
        for sample_index, timestamp in enumerate(timestamps, start=1):
            suffix = "final" if sample_index == len(timestamps) else f"key{sample_index:02d}"
            output = out_dir / f"scene{index:02d}-{suffix}.png"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-ss",
                    f"{timestamp:.3f}",
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    str(output),
                ]
            )
            stills.append(output)
            manifest.append(
                {
                    "scene": index,
                    "sample": sample_index,
                    "path": str(output),
                    "source_video": str(path),
                    "timestamp_seconds": round(timestamp, 3),
                    "scene_duration_seconds": round(duration, 3),
                }
            )
            print(f"scene {index} sample {sample_index}: {output} at {timestamp:.2f}s of {duration:.2f}s")
    (out_dir / "keyframes.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return stills, manifest


def make_contact_sheet(
    stills: list[Path],
    output: Path,
    *,
    thumb_width: int,
    gap: int,
) -> None:
    if not stills:
        return
    columns = min(4, len(stills))
    source_width, source_height = ffprobe_dimensions(stills[0])
    thumb_height = max(1, round(source_height * thumb_width / source_width))
    inputs: list[str] = []
    for still in stills:
        inputs.extend(["-i", str(still)])

    scale_filters = [
        f"[{index}:v]scale={thumb_width}:{thumb_height}[v{index}]"
        for index in range(len(stills))
    ]
    stack_inputs = "".join(f"[v{index}]" for index in range(len(stills)))
    layout = "|".join(
        f"{(index % columns) * (thumb_width + gap)}_{(index // columns) * (thumb_height + gap)}"
        for index in range(len(stills))
    )
    filter_graph = ";".join(scale_filters) + (
        f";{stack_inputs}xstack=inputs={len(stills)}:layout={layout}:fill=0x101418[out]"
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            *inputs,
            "-filter_complex",
            filter_graph,
            "-map",
            "[out]",
            str(output),
        ]
    )
    print(f"contact sheet: {output}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concat", type=Path, default=Path("concat.txt"))
    parser.add_argument("--out-dir", type=Path, default=Path("review-stills"))
    parser.add_argument("--offset", type=float, default=0.6)
    parser.add_argument("--samples-per-scene", type=int, default=3)
    parser.add_argument("--thumb-width", type=int, default=426)
    parser.add_argument("--gap", type=int, default=12)
    args = parser.parse_args()

    paths = parse_concat(args.concat)
    if not paths:
        raise SystemExit(f"No scene files found in {args.concat}")
    stills, _manifest = extract_stills(
        paths,
        args.out_dir,
        args.offset,
        args.samples_per_scene,
    )
    make_contact_sheet(
        stills,
        args.out_dir / "contact-sheet.png",
        thumb_width=args.thumb_width,
        gap=args.gap,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
