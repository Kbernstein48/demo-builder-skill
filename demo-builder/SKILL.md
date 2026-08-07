---
name: demo-builder
description: Build or revise narrated Manim demos, product-flow animations, architecture explainers, process walkthroughs, and storyboard/keyframe review packages. Use for script-first approval, cue-locked timing, UiPath brand discovery, reusable enterprise visual design, still-only pre-render review, deterministic layout checks, ElevenLabs or approved fallback voiceover, final rendering, and complete-video visual/audio QA.
---

# Demo Builder

## Purpose

Create source-grounded Manim explainers with a reusable talk track, visible causal story, cue-level synchronization, and a review loop that catches both final-state and transition defects.

Use UiPath branding by default. If the user requests another brand or an unbranded film, follow that request and record the tradeoff in `plan.md`. Never carry nouns, personas, product claims, logos, or process steps from an unrelated project.

Never hard-code credentials. Load TTS keys from environment variables or a local `.env`; do not echo a key supplied in chat or write it into generated files.

## Production Modes And Hard Gates

Infer the narrowest mode that satisfies the request:

- **Script-first**: create `plan.md`, `talk_track.md`, `voiceover_script.md`, and `voiceover_cues.json`; stop for approval when requested.
- **Storyboard-only**: build cue-locked scenes and complete-video keyframes without rendering a video.
- **Full production**: continue through measured narration, final rendering, muxing, and verification.

Treat instructions such as “show me the script first,” “send every keyframe before rendering,” or “do not render yet” as hard gates. Still-only Manim execution and image capture are allowed before a render gate; do not create a draft or final video until the gate is cleared.

## Core Workflow

1. **Ground the story**: inspect the user’s docs, repos, screenshots, recordings, and described flow. Record confirmed facts, future-state claims, actors, state transitions, decision boundaries, and result contracts.
2. **Discover the brand**: load `$uipath-branding` for UiPath work. Read its required design references and this skill’s `references/uipath-video-design-language.md` before visual planning.
3. **Plan and script**: write `plan.md`, `talk_track.md`, `voiceover_script.md`, and `voiceover_cues.json`. Include audience, misconception, aha moment, scene spine, visual grammar, truth boundaries, timing budget, and the question each scene answers.
4. **Honor script approval**: if the user requested script review, present the script and stop before animation work.
5. **Compile estimated timing**: copy and run `scripts/build_cue_timeline.py`. Use the generated `timeline.json` as the single timing source for Manim and narration.
6. **Build cue-locked scenes**: use one independently renderable class per scene. Copy `assets/cue_timeline.py` and `assets/uipath_manim_helpers.py` into the project and adapt them rather than rebuilding timing and QA primitives.
7. **Run storyboard mode**: execute Manim with `-s` at 1080p, capture every cue settle plus onset/focus/land boundaries for risky transitions, and build scene and complete-video sheets with `scripts/build_storyboard_sheets.py`.
8. **Review and correct**: inspect the complete-video keyframe sheet, every changed scene, and individual event-boundary frames with `view_image`. Patch and recapture only affected scenes, then rebuild the complete-video sheet to catch regressions elsewhere.
9. **Honor render approval**: if rendering is gated, present the complete keyframe package and stop.
10. **Generate and lock narration**: synthesize one raw clip per cue, measure it, rebuild timing with `build_cue_timeline.py --from-raw`, and adjust wording or animation rather than aggressively speeding speech.
11. **Render and verify**: render scenes, stitch with ffmpeg, mux narration, verify streams, duration, loudness, and frame drift, then repeat complete-video visual QA after any material change.

## Required Story And Truth Rules

- Build a causal spine: pain → old limit → new mechanism → proof → transfer → recap.
- Make every major claim visible. Show what changed and why the outcome changed.
- Preserve the user-approved framing; add requested concepts surgically unless a rewrite is explicitly requested.
- Label current, demonstrated, inferred, and future-state capabilities when the distinction matters.
- Do not let a retrieval result, graph, model, or agent visually imply authority it does not possess.
- End on the mechanism and takeaway, not a bare list of examples.

## Cue Contract

Use one cue per spoken visual beat. Each cue must include an ID, name, text, and visual event ID. The compiled timeline should expose:

```text
onset → focus → land → settle
```

Drive scene animations through `CueClock`; fail when cue motion drifts by more than one source-timeline frame. Split transitions at `focus` when two text-bearing structures share a lane: remove the old structure first, then introduce the new one. Never rely on a simultaneous crossfade to hide overlapping text.

## Manim And Layout Rules

- Use a stable 16:9 grid, fixed-size objects, known text boxes, and reusable components.
- Set geometry before text; fit text into the geometry rather than allowing text to redefine layout.
- Keep connectors behind opaque cards and attach them to declared border ports.
- Run safe-area, peer-overlap, text-containment, connector-clearance, and connector-crossing assertions in scene code.
- Keep every cue settle screenshot-ready; remove temporary pulses, trails, labels, and updaters unless they communicate the settled state.
- Use motion to explain transformations, handoffs, contrasts, and state changes—not to decorate a static slide.
- Use visual metaphors when they clarify causality, but preserve technical truth.

Read `references/architecture-and-graph-scenes.md` for architecture diagrams, knowledge graphs, complex connectors, progressive disclosure, or physical transformation metaphors. Read `references/3b1b-manim-patterns.md` for complex transforms, coordinate scenes, or 3D camera work.

## Narration

- Always create `talk_track.md`, even when TTS is unavailable.
- Draft concise cue narration before animation, compile estimated timing at roughly 130–150 WPM, then lock to measured raw audio later.
- Prefer the user’s chosen voice and model. Otherwise discover available ElevenLabs voices and use a suitable narrator; treat `Max` as a preference, not a requirement.
- Describe delivery traits rather than imitating a named real person. For example: “warm, resonant, patient science-documentary delivery with a sense of discovery.”
- Rewrite dense narration or allocate more cue time before using speed adjustment.
- Use ElevenLabs by default. Use OpenAI only when requested or after the user approves fallback.

Read `references/narration-and-review.md` before generating speech or performing final media verification.

## Visual Review Contract

Do not call a film final based on successful rendering.

- Capture every cue’s settle frame.
- Capture onset/focus/land for transforms, graph builds, arrows, multiple panels, or text replacements.
- Inspect individual 1920×1080 frames whenever a contact sheet is dense.
- Inspect the complete-video sheet after changing one scene; unchanged scenes can still contain latent defects.
- Reject clipped or overlapping text, lines through text, connectors entering unrelated cards, unclear arrow direction, detached labels, blank/frozen beats, and frames that depend on narration to make basic sense.
- Re-run both scene-local and complete-video QA after a fix.

## Project Shape

```text
demo-name/
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
  concat.txt
  sync-events/
  review-storyboard/
    all-cues/
    events/
    sheets/
  narration/
  media/
  final.mp4
  final_narrated.mp4
```

Ignore generated `media/`, narration downloads, `.venv/`, `__pycache__/`, `*.pyc`, and temporary storyboard media when packaging source.

## Bundled Tools

- `scripts/build_cue_timeline.py`: compile estimated or raw-audio-locked frame timing, narration manifest, audio lock, and sync report.
- `scripts/build_storyboard_sheets.py`: create per-scene, complete-video, and curated keyframe sheets from cue-settle captures.
- `scripts/extract_scene_stills.py`: sample already-rendered scene videos when cue capture is unavailable.
- `scripts/generate_elevenlabs_voiceover.py`: generate and mux ElevenLabs narration.
- `scripts/generate_openai_voiceover.py`: approved OpenAI fallback.
- `assets/cue_timeline.py`: reusable cue clock and still/event capture layer.
- `assets/uipath_manim_helpers.py`: UiPath visual primitives and deterministic layout assertions.

## Final Handoff

Report the highest completed gate, relevant artifact paths, narration provider/model/voice when generated, timing mode and duration, validation results, and anything intentionally not rendered or not verified.

