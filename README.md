# Demo Builder

`demo-builder` is a Codex skill for creating source-grounded, narrated Manim explainers. It supports product-flow animations, architecture explainers, process walkthroughs, and cue-level storyboard review.

The skill is built around a causal story, cue-locked timing, deterministic layout checks, and visual review before final rendering.

## Production modes

- **Script-first** — prepares the plan, talk track, narration script, and cue manifest, then stops for approval.
- **Storyboard-only** — builds cue-locked scenes and complete-video keyframes without rendering a video.
- **Full production** — generates narration, locks timing to measured audio, renders the scenes, muxes the result, and performs visual and audio QA.

## Install

Clone this repository and copy the complete `demo-builder/` directory into your Codex skills directory:

```bash
gh repo clone KevinBernstein-UiPath/demo-builder-skill
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R demo-builder-skill/demo-builder "${CODEX_HOME:-$HOME/.codex}/skills/demo-builder"
```

Restart Codex after installing the skill.

This is a private repository, so the GitHub account used by `gh` must have access.

## Requirements

- Codex with local skill support
- Python 3
- [Manim Community](https://www.manim.community/)
- `ffmpeg` and `ffprobe`
- The `uipath-branding` skill for UiPath-branded demos
- An `ELEVENLABS_API_KEY` environment variable when generating ElevenLabs narration
- An `OPENAI_API_KEY` environment variable only when using the approved OpenAI narration fallback

Never place credentials in scripts, plans, manifests, or committed files.

## Use

Ask Codex to invoke `$demo-builder` and state the production gate you want.

Script-first example:

```text
Use $demo-builder to plan a three-minute architecture explainer. Show me the complete script before creating animation scenes.
```

Storyboard-only example:

```text
Use $demo-builder to build this process walkthrough. Capture every cue and risky transition, but do not render a video yet.
```

Full-production example:

```text
Use $demo-builder to create the narrated Manim demo, lock timing to the generated audio, render it, and complete visual and audio QA.
```

## What the skill produces

A full demo project can include:

```text
plan.md
talk_track.md
voiceover_script.md
voiceover_cues.json
timeline.json
voiceover_segments.json
audio_lock.json
sync_report.md
cue_timeline.py
script.py
manim.cfg
render.sh
review-storyboard/
narration/
media/
final.mp4
final_narrated.mp4
```

Generated media, narration downloads, virtual environments, bytecode, and temporary storyboard media are not part of the source package.

## Repository contents

```text
demo-builder/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── cue_timeline.py
│   └── uipath_manim_helpers.py
├── references/
│   ├── 3b1b-manim-patterns.md
│   ├── architecture-and-graph-scenes.md
│   ├── narration-and-review.md
│   └── uipath-video-design-language.md
└── scripts/
    ├── build_cue_timeline.py
    ├── build_storyboard_sheets.py
    ├── extract_scene_stills.py
    ├── generate_elevenlabs_voiceover.py
    └── generate_openai_voiceover.py
```

See [`demo-builder/SKILL.md`](demo-builder/SKILL.md) for the complete workflow, truth rules, cue contract, layout constraints, narration policy, and final verification requirements.
