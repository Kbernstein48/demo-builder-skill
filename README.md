# Demo Builder and UiPath Branding

This repository bundles two complementary Codex skills:

| Skill | Purpose |
|---|---|
| [`demo-builder`](demo-builder/SKILL.md) | Creates source-grounded, narrated Manim explainers with cue-locked timing, deterministic layout checks, and complete-video review. |
| [`uipath-branding`](uipath-branding/SKILL.md) | Applies UiPath Brand Book V3.3 guidance and provides the approved reference material, logos, icons, and example imagery used by branded demos. |

`demo-builder` loads `uipath-branding` when producing UiPath work, so installing both skills keeps the animation workflow and its design language together.

## Install

Clone this repository and copy both complete skill directories into your Codex skills directory:

```bash
gh repo clone KevinBernstein-UiPath/demo-builder-skill
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R demo-builder-skill/demo-builder "${CODEX_HOME:-$HOME/.codex}/skills/demo-builder"
cp -R demo-builder-skill/uipath-branding "${CODEX_HOME:-$HOME/.codex}/skills/uipath-branding"
```

Restart Codex after installing the skill.

This is a private repository, so the GitHub account used by `gh` must have access.

## Demo Builder

### Production modes

- **Script-first** — prepares the plan, talk track, narration script, and cue manifest, then stops for approval.
- **Storyboard-only** — builds cue-locked scenes and complete-video keyframes without rendering a video.
- **Full production** — generates narration, locks timing to measured audio, renders the scenes, muxes the result, and performs visual and audio QA.

### Requirements

- Codex with local skill support
- Python 3
- [Manim Community](https://www.manim.community/)
- `ffmpeg` and `ffprobe`
- The bundled `uipath-branding` skill for UiPath-branded demos
- An `ELEVENLABS_API_KEY` environment variable when generating ElevenLabs narration
- An `OPENAI_API_KEY` environment variable only when using the approved OpenAI narration fallback

Never place credentials in scripts, plans, manifests, or committed files.

### Use

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

### What it produces

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

## UiPath Branding

Use `$uipath-branding` when creating or reviewing UiPath-branded presentations, documents, apps, websites, campaigns, reports, social assets, events, or other visual materials.

```text
Use $uipath-branding to review this presentation for color, typography, logo, imagery, and CTA compliance.
```

The skill includes:

- Condensed Brand Book V3.3 requirements and reusable design-language guidance
- The source UiPath Brand Book V3.3 PDF
- Official corporate logo variants for digital and print use
- Searchable white and dark-grey 96 px SVG icon libraries
- Rendered examples covering layout, typography, color, photography, reports, and documents

The bundle does not include separate official fonts, templates, Otto artwork, glyph sets, lockups, or other Brand Center production assets. Use approved assets supplied by the user or obtain them through UiPath Brand Center or Creative Studio.

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

uipath-branding/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   ├── example-images/
│   ├── icons/
│   └── logos/
└── references/
    ├── source/uipath-brand-book-v3.3.pdf
    ├── brand-requirements.md
    ├── design-language.md
    ├── example-images.md
    ├── icon-assets.md
    ├── icon-index.md
    ├── icon-index.json
    └── logo-assets.md
```

See each skill's `SKILL.md` for its complete workflow and rules.
