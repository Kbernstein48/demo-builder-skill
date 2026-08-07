#!/usr/bin/env python3
"""Generate a cue-timed ElevenLabs TTS voiceover and mux it onto a rendered video."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


BASE_SCRIPT = Path("/Users/kevin.bernstein/.codex/skills/demo-builder/scripts/generate_openai_voiceover.py")
DEFAULT_MODEL = "eleven_v3"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
DEFAULT_NARRATOR_VOICE_NAME = "Max"
OPENAI_VOICE_NAMES = {
    "alloy",
    "ash",
    "ballad",
    "cedar",
    "coral",
    "echo",
    "fable",
    "marin",
    "nova",
    "onyx",
    "sage",
    "shimmer",
    "verse",
}


def load_base_module():
    spec = importlib.util.spec_from_file_location("demo_builder_openai_voiceover", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Unable to load base voiceover script: {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def api_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVEN_LABS_API_KEY")
    if not key:
        raise SystemExit("ELEVENLABS_API_KEY is not set.")
    return key


def load_simple_env_files(extra_paths: list[Path]) -> None:
    script_dir = Path(__file__).resolve().parent
    candidates = [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        script_dir / ".env",
        script_dir.parent / ".env",
        *extra_paths,
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        for raw_line in resolved.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def request_json(url: str, key: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"xi-api-key": key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ElevenLabs API error {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"ElevenLabs API request failed: {exc}") from None


def post_audio(url: str, key: str, payload: dict[str, Any], output_path: Path) -> None:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "xi-api-key": key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"ElevenLabs API error {exc.code}: {detail}") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"ElevenLabs API request failed: {exc}") from None


def load_voices(key: str) -> list[dict[str, Any]]:
    voices: list[dict[str, Any]] = []
    next_page_token: str | None = None
    while True:
        params = {"page_size": "100", "include_total_count": "false"}
        if next_page_token:
            params["next_page_token"] = next_page_token
        url = "https://api.elevenlabs.io/v2/voices?" + urllib.parse.urlencode(params)
        payload = request_json(url, key)
        page_voices = payload.get("voices", [])
        if not isinstance(page_voices, list):
            raise SystemExit("Unexpected ElevenLabs voices response.")
        voices.extend([voice for voice in page_voices if isinstance(voice, dict)])
        next_page_token = payload.get("next_page_token")
        if not payload.get("has_more") or not next_page_token:
            break
    if not voices:
        raise SystemExit("No ElevenLabs voices are available for this account.")
    return voices


def normalized(value: Any) -> str:
    return str(value or "").strip().casefold()


def choose_voice(
    voices: list[dict[str, Any]],
    desired_name: str,
    *,
    fallback_id: str | None = None,
) -> tuple[str, str]:
    if fallback_id:
        return fallback_id, f"id:{fallback_id}"

    desired = normalized(desired_name)
    for voice in voices:
        if normalized(voice.get("name")) == desired:
            return str(voice["voice_id"]), str(voice.get("name", desired_name))
    for voice in voices:
        if desired and desired in normalized(voice.get("name")):
            return str(voice["voice_id"]), str(voice.get("name", desired_name))

    fallback = voices[0]
    return str(fallback["voice_id"]), str(fallback.get("name", "first available voice"))


def voice_name_from_manifest(raw: dict[str, Any]) -> str | None:
    for field in ("elevenlabs_voice_name", "voice_name"):
        if raw.get(field):
            return str(raw[field])
    voice = str(raw.get("voice", "")).strip()
    if voice and voice.casefold() not in OPENAI_VOICE_NAMES:
        return voice
    return None


def voice_settings(raw: dict[str, Any]) -> dict[str, Any]:
    def number(field: str, default: float) -> float:
        try:
            return float(raw.get(field, os.environ.get(f"ELEVENLABS_{field.upper()}", default)))
        except (TypeError, ValueError):
            return default

    settings = {
        "stability": number("stability", 0.58),
        "similarity_boost": number("similarity_boost", 0.82),
        "style": number("style", 0.24),
        "use_speaker_boost": True,
    }
    speed = raw.get("tts_speed", raw.get("speed", os.environ.get("ELEVENLABS_SPEED")))
    if speed is not None:
        try:
            settings["speed"] = float(speed)
        except (TypeError, ValueError):
            pass
    return settings


def raw_manifest_by_index(path: Path) -> dict[int, dict[str, Any]]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise SystemExit("Manifest must be a JSON array.")
    indexed: dict[int, dict[str, Any]] = {}
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"Segment {index} must be a JSON object.")
        indexed[index] = item
    return indexed


def generate_raw_audio(
    base,
    segments,
    raw_manifest: dict[int, dict[str, Any]],
    raw_dir: Path,
    download_dir: Path,
    *,
    key: str,
    voices: list[dict[str, Any]],
    model: str,
    output_format: str,
    default_voice_id: str | None,
    default_voice_name: str,
    overwrite: bool,
) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)
    default_resolved_id, default_resolved_name = choose_voice(
        voices,
        default_voice_name,
        fallback_id=default_voice_id,
    )
    if default_resolved_name.casefold() != default_voice_name.casefold() and not default_voice_id:
        print(f"voice '{default_voice_name}' not found; using '{default_resolved_name}'")

    previous_text = ""
    for segment in segments:
        raw = raw_manifest[segment.index]
        if not segment.text:
            print(f"silence cue: {segment.label}")
            continue

        output_path = raw_dir / f"{segment.stem}.wav"
        if output_path.exists() and not overwrite:
            print(f"raw exists: {output_path}")
            previous_text = segment.text
            continue

        explicit_voice_id = raw.get("elevenlabs_voice_id") or raw.get("voice_id")
        desired_name = voice_name_from_manifest(raw) or default_voice_name
        voice_id, voice_name = choose_voice(
            voices,
            desired_name,
            fallback_id=str(explicit_voice_id) if explicit_voice_id else None,
        )
        if desired_name.casefold() != voice_name.casefold() and not explicit_voice_id:
            print(f"voice '{desired_name}' not found for {segment.label}; using '{voice_name}'")
            voice_id = default_resolved_id
            voice_name = default_resolved_name

        mp3_path = download_dir / f"{segment.stem}.mp3"
        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/{urllib.parse.quote(voice_id)}?"
            + urllib.parse.urlencode({"output_format": output_format})
        )
        model_id = str(raw.get("elevenlabs_model") or model)
        payload: dict[str, Any] = {
            "text": segment.text,
            "model_id": model_id,
            "voice_settings": voice_settings(raw),
            "apply_text_normalization": "auto",
        }
        supports_text_continuity = model_id != "eleven_v3"
        if previous_text and supports_text_continuity:
            payload["previous_text"] = previous_text
        next_text = str(raw.get("next_text", "")).strip()
        if next_text and supports_text_continuity:
            payload["next_text"] = next_text

        print(f"generating {segment.label} voice={voice_name} model={payload['model_id']}")
        post_audio(url, key, payload, mp3_path)
        base.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-i",
                str(mp3_path),
                "-ac",
                "1",
                "-ar",
                "48000",
                str(output_path),
            ]
        )
        previous_text = segment.text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("voiceover_segments.json"))
    parser.add_argument("--video", type=Path, default=Path("final.mp4"))
    parser.add_argument("--out-dir", type=Path, default=Path("narration/elevenlabs"))
    parser.add_argument("--output", type=Path, default=Path("final_narrated.mp4"))
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--voice-id")
    parser.add_argument("--voice-name")
    parser.add_argument("--output-format")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-voices", action="store_true")
    args = parser.parse_args()

    base = load_base_module()
    env_candidates = [args.manifest.parent / ".env", args.video.parent / ".env", args.output.parent / ".env"]
    if args.env_file:
        env_candidates.insert(0, args.env_file)
    base.load_env_files(env_candidates)
    load_simple_env_files(env_candidates)

    model = args.model or os.environ.get("ELEVENLABS_MODEL", DEFAULT_MODEL)
    default_voice_name = args.voice_name or os.environ.get("ELEVENLABS_VOICE_NAME", DEFAULT_NARRATOR_VOICE_NAME)
    default_voice_id = args.voice_id or os.environ.get("ELEVENLABS_VOICE_ID")
    output_format = args.output_format or os.environ.get("ELEVENLABS_OUTPUT_FORMAT", DEFAULT_OUTPUT_FORMAT)

    base.require_tool("ffmpeg")
    base.require_tool("ffprobe")
    segments = base.load_segments(args.manifest)
    if not args.video.exists():
        raise SystemExit(f"Missing video: {args.video}")

    if args.dry_run:
        base.dry_run(segments, args.video)
        print(f"default ElevenLabs model: {model}")
        print(f"default narrator voice preference: {default_voice_name}")
        return 0

    key = api_key()
    voices = load_voices(key)
    if args.list_voices:
        for voice in voices:
            print(f"{voice.get('name', '(unnamed)')}: {voice.get('voice_id')}")
        return 0

    raw_manifest = raw_manifest_by_index(args.manifest)
    raw_dir = args.out_dir / "raw"
    download_dir = args.out_dir / "downloads"
    padded_dir = args.out_dir / "padded"
    voiceover_path = args.out_dir / "voiceover.wav"
    concat_path = args.out_dir / "audio_concat.txt"
    video_duration = base.ffprobe_duration(args.video)

    generate_raw_audio(
        base,
        segments,
        raw_manifest,
        raw_dir,
        download_dir,
        key=key,
        voices=voices,
        model=model,
        output_format=output_format,
        default_voice_id=default_voice_id,
        default_voice_name=default_voice_name,
        overwrite=args.overwrite,
    )
    padded_paths = base.pad_and_place_audio(segments, raw_dir, padded_dir, video_duration=video_duration)
    base.concat_audio(padded_paths, concat_path, voiceover_path)
    base.mux_video(args.video, voiceover_path, args.output)

    output_duration = base.ffprobe_duration(args.output)
    audio_duration = base.ffprobe_duration(voiceover_path)
    print(f"voiceover: {voiceover_path} ({audio_duration:.2f}s)")
    print(f"muxed video: {args.output} ({output_duration:.2f}s, source {video_duration:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
