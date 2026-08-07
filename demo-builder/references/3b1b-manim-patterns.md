# 3Blue1Brown Manim Patterns

Distilled from the 3b1b Manim docs at `https://github.com/3b1b/manim/tree/master/docs`. These are design and workflow patterns, not a mandate to use `manimlib`. Prefer Manim CE APIs for new projects unless the target project already uses 3b1b Manim.

## What Transfers Across Manim Lineages

- A video is a sequence of `Scene` subclasses. Each scene defines `construct()`.
- Static setup uses `self.add(...)`; motion uses `self.play(...)`; pacing uses `self.wait(...)`.
- The visual object model is mobject-first: create mobjects, position/style/group them, then animate changes.
- Animate method calls with `.animate` where available: `mob.animate.shift(RIGHT)`, `mob.animate.set_color(YELLOW)`, `tracker.animate.set_value(4)`.
- Use transforms to preserve visual continuity: `ReplacementTransform`, `TransformMatchingTex`, `TransformMatchingShapes`, and fade transforms where available.
- Use final-frame or still rendering for fast layout review before long renders.
- Use config/CLI quality settings for iteration: low quality for drafts, higher quality only after layout passes.

## Scene Planning Patterns

Plan scenes by the change they reveal:

- **Boundary**: a process reaches a hard edge.
- **Handoff**: one actor transfers bounded work to another.
- **Contract**: context flows in, structured result flows out.
- **Split ownership**: lanes or columns show who owns which part.
- **Loop closure**: ambiguity resolves and deterministic automation resumes.
- **Continuity transform**: the same object changes form to preserve viewer memory.

Each scene should have one dominant question and one visual answer.

## Mobject Composition

- Use `VGroup`/`Group` for panels, timelines, rows, and repeated cards.
- Use `arrange`, `next_to`, `align_to`, `to_edge`, and `to_corner` instead of raw coordinates whenever possible.
- Use fixed dimensions for cards, icons, lanes, and timeline nodes so labels cannot resize the layout.
- Use `SurroundingRectangle`, `Brace`, `Arrow`, `DashedLine`, and labels to annotate relationships, not to decorate.
- Use dim rails, grids, or lanes as structure at low opacity; reserve full opacity for the current focus.

## Timing

- Treat `self.play` and `self.wait` calls as the edit timeline.
- Add a wait after every reveal that changes the viewer's understanding.
- For narration, leave a small silence margin at the end of each scene so the next scene does not feel clipped.
- Prefer one class per scene and one audio segment per scene.

## Transform Matching

Use matching transforms when a concept is being rearranged rather than replaced.

- Math or formula continuity: `TransformMatchingTex`.
- Text/shape continuity: `TransformMatchingShapes`.
- Business demo continuity: convert the same case packet, contract, or actor node through multiple states instead of fading unrelated objects in and out.

When transform matching is brittle, split text into deliberate submobjects or use simpler `ReplacementTransform`/`FadeTransform` pairs.

## Updaters And Trackers

Use live-updating objects for demos that show changing values, progress, or current focus.

- `ValueTracker` drives a numeric value over time.
- `always_redraw` rebuilds a dependent mobject each frame.
- `add_updater` is useful for labels that must follow moving objects.
- Clear or avoid updaters before a scene cleanup if they are no longer needed.

Good demo uses:

- Highlight dot following a graph or timeline.
- Counter changing as documents, tasks, or cases progress.
- Braces or labels tracking a moving or resizing object.
- Camera-follow label or current-step badge.

## Coordinates, Graphs, And Timelines

The 3b1b docs emphasize coordinate systems and graph transitions. For non-math demos, reuse the same discipline:

- Treat a timeline as a coordinate system with explicit anchors.
- Treat each case state as a point on a path.
- Use axes or lanes when the viewer must compare dimensions.
- Use one moving indicator to show current time, state, or ownership.

For actual graphs, use `Axes`, coordinate conversion helpers, graph labels, and `ValueTracker` to move points along curves.

## 3D And Camera

Use 3D only when depth explains the system better than 2D.

- Keep labels fixed in frame when they must remain readable during camera motion.
- Move the camera frame deliberately and slowly; avoid gratuitous orbiting.
- Review rendered frames, because 3D perspective can hide text and overlap objects.
- If the user requests 3D, also follow frontend-style visual verification: desktop/mobile is irrelevant, but nonblank canvas, framing, and motion still matter.

## Interaction And Development

3b1b Manim supports interactive scene development; Manim CE workflows differ, but the principle transfers:

- Iterate in low quality.
- Render one scene at a time.
- Use final-frame stills to inspect layout.
- Use animation-number skipping or scene-specific renders when debugging.
- Keep helper functions small enough that a scene can be rendered independently.

## API Caution

3b1b Manim docs use `from manimlib import *`, `ShowCreation`, `TexText`, `OldTex`, and `manimgl`. Manim CE uses `from manim import *`, `Create`, `Text`/`Tex`/`MathTex`, and `manim`. Translate idioms to the local engine instead of copying code blindly.
