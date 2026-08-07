# Narration And Review

Use this reference when a demo video needs voiceover, synchronized narration, image-recognition key-frame review, or audio/video validation.

## Voiceover Workflow

1. Write `talk_track.md` for every demo, even when generated TTS is not possible. It should be a presenter-ready narrative with the story spine, scene-by-scene talking points, and the objections or partner questions each scene answers.
2. Write `voiceover_script.md` and `voiceover_cues.json` before animation. Use one cue per visible spoken beat.
3. If the user requested script approval, stop before animation work.
4. Compile estimated cue timing with `scripts/build_cue_timeline.py`.
5. Build and review cue-locked keyframes without rendering video when a render gate is active.
6. Generate one raw TTS clip per spoken cue. Use ElevenLabs by default unless the user requests another provider.
7. Measure raw audio and rebuild the timeline with `build_cue_timeline.py --from-raw`.
8. Rewrite dense cues or allocate more animation time before applying speed adjustment.
9. Render and stitch the audio-locked silent video.
10. Normalize/pad clips to their absolute cue windows, concatenate `voiceover.wav`, and mux `final_narrated.mp4`.
11. Verify duration, frame drift, audio/video streams, and volume.

## Cue Source Schema

Use `voiceover_cues.json` as the authored source for timing:

```json
{
  "fps": 60,
  "voice_style": "Warm, precise enterprise narration.",
  "scenes": [
    {
      "id": "S00_Opening",
      "title": "Opening",
      "cues": [
        {
          "id": "opening.problem",
          "name": "Problem",
          "visual_event_id": "problem.reveal",
          "text": "The path is clear until an exception appears."
        }
      ]
    }
  ]
}
```

Cue IDs must be unique within a scene. Keep cue text in the same order as `voiceover_script.md`; the timeline compiler fails when the script and cue text drift.

## Generated Manifest Schema

Use seconds as numbers, not strings.

```json
[
  {
    "scene": 1,
    "cue": 1,
    "name": "Opening claim",
    "start_seconds": 0.0,
    "end_seconds": 5.2,
    "target_audio_seconds": 4.7,
    "text": "Narration for this cue."
  },
  {
    "scene": 1,
    "cue": 2,
    "name": "Silent beat",
    "start_seconds": 5.2,
    "end_seconds": 6.0,
    "target_audio_seconds": 0.6,
    "text": ""
  },
  {
    "scene": 1,
    "cue": 3,
    "name": "Second reveal",
    "start_seconds": 6.0,
    "end_seconds": 12.2,
    "target_audio_seconds": 5.5,
    "text": "Narration for the next reveal."
  }
]
```

`target_audio_seconds` should be shorter than `end_seconds - start_seconds` unless the cue is intentionally voice-dense. `cue` is optional but recommended for readability; if omitted, cues are numbered within each scene. Unknown fields are ignored, so the manifest can include notes for humans.

Use absolute times from the beginning of `final.mp4`. Segments must not overlap. If there is a gap between one cue's `end_seconds` and the next cue's `start_seconds`, the TTS scripts insert silence to preserve synchronization.

Optional provider fields:

- `speaker`: human-readable role such as `Narrator`, `Caller`, `Agent`, or `System`.
- `voice_style`: direction for rewriting or choosing delivery.
- `elevenlabs_voice_id`: exact ElevenLabs voice ID for a cue.
- `elevenlabs_voice_name` or `voice_name`: ElevenLabs voice name for a cue.
- `elevenlabs_model`: cue-level ElevenLabs model override.
- `tts_speed`: cue-level speech speed where the provider supports it.

## Narration Writing

- Write for the current demo source, not for a generic product category.
- Use short sentences that can survive synthetic narration.
- Avoid dense lists unless the visual shows the list while it is spoken.
- Keep narration close to the visual build order. If a scene has three major reveals, use three cue rows instead of one dense scene paragraph.
- Aim for 130-150 words per minute for enterprise/product demos.
- Use explicit actor names and state names when the demo flow depends on them.
- If a scene is visually dense, say less and let the visual carry it.
- Describe delivery traits instead of requesting an imitation of a real person.

## TTS Provider Selection

Use ElevenLabs by default for polished narrated demos. If ElevenLabs credentials are missing, stop and report the missing variable unless the user explicitly approves a fallback provider.

- **ElevenLabs**: default for polished narration and dialogue voices. Honor an explicit user voice/model first. Otherwise discover account voices and prefer `Max` when it suits the requested delivery; do not force it over a better cue-specific choice.
- **OpenAI Speech API**: useful fallback when the user asks for OpenAI, wants promptable tone, or already has the OpenAI stack configured.
- **Azure AI Speech**: enterprise controls, SSML, and Microsoft estate fit.
- **Google Cloud Text-to-Speech**: broad language/voice coverage and SSML.
- **Amazon Polly**: AWS-native, predictable, and common in regulated environments.
- **Local TTS**: useful for private or offline drafts, usually lower demo polish.

## ElevenLabs TTS

Use the bundled script:

```bash
python /Users/kevin.bernstein/.codex/skills/demo-builder/scripts/generate_elevenlabs_voiceover.py \
  --manifest voiceover_segments.json \
  --video final.mp4 \
  --output final_narrated.mp4
```

The script uses the ElevenLabs REST API, discovers available voices, prefers narrator voice name `Max`, falls back to the first available voice, downloads MP3 generations, converts raw clips to WAV, pads each cue to the exact timing window, and muxes the finished audio onto the video.

Set credentials through the environment or `.env`:

```text
ELEVENLABS_API_KEY=...
ELEVENLABS_MODEL=eleven_v3
ELEVENLABS_VOICE_NAME=Max
```

Never hard-code `ELEVENLABS_API_KEY` in this skill, generated scripts, manifests, plans, talk tracks, or project files. If credentials are missing, keep the talk track and voiceover manifest, run `--dry-run` when possible, and report the missing variable.

Useful options:

```bash
python /Users/kevin.bernstein/.codex/skills/demo-builder/scripts/generate_elevenlabs_voiceover.py \
  --manifest voiceover_segments.json \
  --video final.mp4 \
  --dry-run

python /Users/kevin.bernstein/.codex/skills/demo-builder/scripts/generate_elevenlabs_voiceover.py \
  --list-voices
```

Do not print API keys. If the script fails with missing credentials, report the missing variable and stop.

## OpenAI TTS

Use this only when the user requests OpenAI or approves it as a fallback. Use the bundled script:

```bash
python /Users/kevin.bernstein/.codex/skills/demo-builder/scripts/generate_openai_voiceover.py \
  --manifest voiceover_segments.json \
  --video final.mp4 \
  --output final_narrated.mp4
```

Install dependencies in the project venv:

```bash
python -m pip install openai python-dotenv
```

Set credentials through the environment or `.env`:

```text
OPENAI_API_KEY=...
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=cedar
```

Do not print API keys. If the script fails with missing credentials, report the missing variable and stop.

## Image-Recognition Key-Frame Review

For cue-locked projects, capture frames directly during still-only Manim execution. Save every cue settle and onset/focus/land boundaries for risky transitions, then build scene and complete-video sheets with `scripts/build_storyboard_sheets.py`. This is the preferred pre-render path.

Use the bundled extractor after rendering or when a project does not use cue capture:

```bash
python /Users/kevin.bernstein/.codex/skills/demo-builder/scripts/extract_scene_stills.py \
  --concat concat.txt \
  --out-dir review-stills \
  --samples-per-scene 3
```

It writes:

- `review-stills/contact-sheet.png`
- `review-stills/keyframes.json`
- `review-stills/sceneNN-keyMM.png` and `review-stills/sceneNN-final.png`

Inspect the complete-video sheet with `view_image` first. Then inspect individual 1920×1080 frames whenever the sheet is dense, a transition replaces text, or any scene looks questionable. After fixing one scene, rebuild the complete-video sheet; unchanged scenes may still contain latent defects.

Review questions:

- Is all text readable at the rendered resolution?
- Is any text clipped, overlapped, or too close to the edge?
- Do arrows, timelines, lanes, and connectors imply the intended sequence?
- Do labels stay attached to the right objects?
- Does each scene's final state match the narration and source material?
- Do intermediate frames show awkward partial states, hidden labels, or collisions?
- Are colors, opacity, and visual salience directing attention correctly?
- Are any frames blank, frozen, or visually redundant?
- Do onset, focus, land, and settle frames remain clean through the transition?
- Does any simultaneous crossfade place two text-bearing structures in the same lane?

Fix:

- text overlap
- off-frame labels
- too-small text
- incoherent arrows or paths
- unreadable contrast
- visual states that do not match the narration
- scenes that do not progress the demo flow

After fixes, recapture affected scenes, rebuild the complete-video sheet, and inspect again. After final rendering, re-stitch if necessary and repeat visual QA. Do not finalize a video without both pre-render keyframe approval and post-render inspection when the user requested an approval gate.

## Review Notes Template

Use concise working notes while reviewing:

```text
Frame: review-stills/scene03-key02.png
Issue: timeline label overlaps connector at lower right
Fix: reduce label font to 18 and move connector down by 0.25
Status: fixed and re-rendered
```

## Media Verification Commands

Check streams and duration:

```bash
ffprobe -v error -show_entries format=duration,size -show_streams -of json final_narrated.mp4
```

Check audio level:

```bash
ffmpeg -hide_banner -i final_narrated.mp4 -map 0:a:0 -af volumedetect -f null - 2>&1 | rg 'mean_volume|max_volume'
```

Typical spoken narration should avoid clipping. A peak near `-1 dB` to `-3 dB` is usually fine; if mean volume is too low for a demo, normalize or increase the AAC mix.

## Final Response Checklist

Report:

- final video path
- talk track path
- narration provider/model/voice if generated
- duration and stream verification
- any review stills/contact sheet path if relevant
- tests or commands that could not be run
