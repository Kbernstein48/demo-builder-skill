# UiPath Video Design Language

Use this reference when a demo should carry UiPath brand quality, when no other brand system is specified, or when the user asks for UiPath-styled product, enterprise, or platform videos.

## Brand Discovery Contract

Before planning visuals, perform a UiPath branding discovery pass:

1. Load `$uipath-branding`.
2. Read `references/design-language.md` for practical direction.
3. Read `references/brand-requirements.md` when choosing exact color, type, pixel, CTA, logo, or asset rules.
4. Read `references/logo-assets.md` before placing a UiPath logo.
5. Read icon references only when the video needs official icons.
6. Capture the brand decisions in `plan.md`: palette, typography fallback, pixel usage, motion grammar, and any tradeoffs caused by Manim or missing brand assets.

If the user explicitly asks for a different brand, still note the conflict and follow the user's requested brand. Do not mix UiPath marks into non-UiPath work unless the user asks.

## Baseline Pattern

The conversational-agents demo is the baseline design language:

- Deep Blue canvas with visible but quiet grid structure.
- Robotic Orange for impact, robots, urgency, and business action.
- Agentic Teal for agents, calm guidance, intelligence, and orchestration.
- Bright White for high-contrast text and final takeaways.
- Muted neutrals for context, secondary labels, connectors, and system structure.
- Small pixel motifs in corners or as flow markers, never as filler.
- Reusable objects: title blocks, label cards, pills, waveforms, process rails, entity nodes, connectors, and callout bubbles.
- Animation shows transformations: stress becomes calm, menu trees become dialogue, conversation becomes governed process, one agent projects into many surfaces.

## Grid System

Use a stable 16:9 frame with a visible safe area:

- Keep primary content inside about `12.8 x 7.0` Manim units.
- Use a 12-column by 7-row composition grid for major placement.
- Keep at least `0.5` units from frame edges for titles, labels, and final takeaways.
- Keep at least `0.25` units between unrelated objects and `0.12` inside object padding.
- Use fixed-width components for repeated cards, process steps, pills, and counters.
- Align titles to a top band, diagrams to a middle band, and summaries to a bottom band unless the scene intentionally breaks the pattern.
- Reserve corner pixels for brand texture; never let them compete with the scene's reading order.

When a scene has many elements, prefer lanes and rails over free-floating clusters. Use opacity to demote context rather than adding more labels.

## Reusable Building Blocks

Start from `assets/uipath_manim_helpers.py` when a UiPath-branded Manim video is being built. Copy or adapt its helpers into the project so each scene uses the same object rules.

Required helpers or equivalents:

- `brand_backdrop`: deep-blue canvas, quiet grid, and small pixel motifs.
- `title_block`: kicker, short headline, compact subtitle, and fit-to-width behavior.
- `wrapped_text` and `fit_to_box`: every text object must fit a known width and height.
- `label_card`: fixed-size object cards with internal text scaling.
- `pill`: short status labels and semantic tags.
- `process_rail`: ordered handoffs, timelines, and business processes.
- `waveform`: voice, emotion, signal, and state-change visuals.
- `orthogonal_connector` and `network_link`: border-clipped handoff and graph relationships.
- `assert_no_overlaps`, `assert_safe_area`, `assert_text_contained`, and connector assertions: deterministic guards for important cue states.

Treat these as known-good objects, not a restrictive style kit. A creative scene may add custom metaphors, 3D camera moves, fluid particles, data trails, masks, or character movement, but it should still inherit the same typography, color semantics, safe-area rules, and review gates.

## Text And Object Rules

- Use short headlines. Do not put paragraph copy in the center of a scene.
- Set letter spacing to `0` in code paths that expose it.
- Use Arial as the practical Manim fallback unless brand fonts are available locally.
- Use fixed object dimensions before creating text, then scale text into the object.
- Limit each card to one label and one short supporting line.
- Avoid nested cards. Use bands, lanes, rails, and groups instead.
- Give each object a semantic role: actor, system, tool, process step, status, evidence, or outcome.
- Keep labels attached to objects through transforms. If an object moves, move the label with it in a `VGroup`.
- Check important cue-boundary and final-state layout with helper assertions, then verify visually.

## Animation Defaults

Default to animated explanation, not text slides:

- Show a transformation in every scene: before to after, rough to structured, disconnected to orchestrated, hidden platform to visible proof, or one channel to many channels.
- Use `Transform`, `ReplacementTransform`, `TransformMatchingShapes`, `LaggedStart`, path motion, and updaters to preserve continuity.
- Build attention in layers: stage, actors, signal, action, proof, takeaway.
- Use kinetic brand motifs sparingly: pixel trails, waveforms, process ribbons, scanning highlights, and curtain/stage reveals.
- Make the key claim visible before narrating it or while it is being spoken.
- Keep final frames clean enough to work as screenshots.

## Visual Reinforcement Loop

Run the normal still-extraction review plus a brand-quality pass:

1. Capture every cue settle plus onset/focus/land boundaries for risky transitions.
2. Build per-scene and complete-video sheets after every material visual change.
3. Inspect the complete-video sheet with `view_image`.
4. Inspect individual 1080p frames for dense scenes, small text, arrows, timelines, graphs, or multi-panel layouts.
5. Record concrete fixes, recapture affected scenes, and rebuild the complete-video sheet.
6. Repeat until both content coherence and brand quality pass.

Brand-quality checks:

- UiPath colors carry meaning: orange for impact/robots/action, teal for agents/AI/calm guidance, deep blue for structure, white for clarity.
- The scene has a clear grid, reading order, and whitespace.
- Pixel motifs are intentional and consistently sized.
- Text is readable, not clipped, and not too close to another object or edge.
- Object internals are consistent: same padding, similar type sizes, stable card dimensions.
- Connectors imply the correct sequence and remain attached.
- The frame feels enterprise-ready: confident, direct, polished, and not cluttered.
- The scene still feels creative: it shows motion, reveal, contrast, or metaphor rather than static bullet points.
