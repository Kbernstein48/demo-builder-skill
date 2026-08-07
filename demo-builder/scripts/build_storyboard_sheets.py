#!/usr/bin/env python3
"""Build labeled scene and complete-video sheets from cue-settle captures."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc


BG = "#101418"
PANEL = "#182126"
WHITE = "#FFFFFF"
TEAL = "#5BCBDE"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


TITLE_FONT = font(28, bold=True)
LABEL_FONT = font(18, bold=True)
META_FONT = font(15)


def capture_path(root: Path, scene_id: str, cue_index: int, cue_id: str) -> Path:
    matches = sorted((root / scene_id).glob(f"{cue_index:02d}-{cue_id}-settle.png"))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"Expected one capture for {scene_id}/{cue_id}; found {matches}"
        )
    return matches[0]


def card(scene_number: int, cue_number: int, cue: dict, path: Path) -> Image.Image:
    frame = Image.open(path).convert("RGB")
    frame.thumbnail((640, 360), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (660, 438), PANEL)
    x = (canvas.width - frame.width) // 2
    canvas.paste(frame, (x, 10))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 377), f"{scene_number}.{cue_number}  {cue.get('name', cue['id'])}", font=LABEL_FONT, fill=WHITE)
    draw.text((16, 405), cue["id"], font=META_FONT, fill=TEAL)
    return canvas


def make_sheet(title: str, cards: list[Image.Image], columns: int, output: Path) -> None:
    if not cards:
        return
    rows = math.ceil(len(cards) / columns)
    header = 64
    gap = 12
    width = columns * 660 + (columns + 1) * gap
    height = header + rows * 438 + (rows + 1) * gap
    sheet = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(sheet)
    draw.text((gap, 16), title, font=TITLE_FONT, fill=WHITE)
    for index, frame in enumerate(cards):
        row, column = divmod(index, columns)
        sheet.paste(frame, (gap + column * (660 + gap), header + gap + row * (438 + gap)))
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=95)


def default_curated(scene: dict) -> set[str]:
    cues = scene["cues"]
    if len(cues) <= 3:
        return {cue["id"] for cue in cues}
    indexes = {0, len(cues) // 2, len(cues) - 1}
    return {cues[index]["id"] for index in indexes}


def load_curated(path: Path | None, timeline: dict) -> dict[str, set[str]]:
    if path is None:
        return {scene["id"]: default_curated(scene) for scene in timeline["scenes"]}
    raw = json.loads(path.read_text())
    return {scene_id: set(cue_ids) for scene_id, cue_ids in raw.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeline", type=Path, default=Path("timeline.json"))
    parser.add_argument("--capture-root", type=Path, default=Path("review-storyboard/all-cues"))
    parser.add_argument("--output-root", type=Path, default=Path("review-storyboard/sheets"))
    parser.add_argument("--curated-json", type=Path)
    parser.add_argument("--scene-columns", type=int, default=3)
    parser.add_argument("--keyframe-columns", type=int, default=4)
    args = parser.parse_args()

    timeline = json.loads(args.timeline.read_text())
    curated_ids = load_curated(args.curated_json, timeline)
    args.output_root.mkdir(parents=True, exist_ok=True)
    complete: list[Image.Image] = []
    curated: list[Image.Image] = []

    for scene_number, scene in enumerate(timeline["scenes"], start=1):
        scene_cards: list[Image.Image] = []
        for cue_number, cue in enumerate(scene["cues"], start=1):
            path = capture_path(args.capture_root, scene["id"], cue_number - 1, cue["id"])
            frame = card(scene_number, cue_number, cue, path)
            scene_cards.append(frame)
            complete.append(frame)
            if cue["id"] in curated_ids.get(scene["id"], set()):
                curated.append(frame)
        make_sheet(
            f"SCENE {scene_number} · {scene.get('title', scene['id']).upper()}",
            scene_cards,
            args.scene_columns,
            args.output_root / f"scene-{scene_number:02d}-{scene['id']}.png",
        )

    make_sheet(
        "DEMO BUILDER · COMPLETE-VIDEO STORYBOARD",
        complete,
        args.scene_columns,
        args.output_root / "complete-video-storyboard.png",
    )
    make_sheet(
        "DEMO BUILDER · CURATED VIDEO KEYFRAMES",
        curated,
        args.keyframe_columns,
        args.output_root / "complete-video-keyframes.png",
    )
    print(f"wrote {len(complete)} cue frames and {len(curated)} curated keyframes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

