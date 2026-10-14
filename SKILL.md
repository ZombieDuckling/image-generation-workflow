---
name: image-generation-workflow
description: Use when any agent must generate or verify images.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  category: creative
  hermes:
    tags: [image-generation, agent-agnostic, prompts, verification, assets]
    related_skills: [dev-asset-generation, hermes-image-generation-routing, comfyui]
---

# Image Generation Workflow (agent-agnostic)

A portable pipeline for any agent that must produce images: choose a backend, build the prompt, generate, **verify the file is real**, place it, then deliver it. Nothing here requires a specific agent framework — every step is a shell command or a plain HTTP call.

Core rule: **never report success from the generator's own return value.** A generator can return `success: true` and still write a blank, truncated, or wrong-format file. Success = a verified raster at a known path.

## When to Use

Use this when an agent must:

- generate an image and hand back a file (not a description of one)
- decide which image backend it can actually use here
- check that a generated image worked before shipping or sending it
- produce hero art, icons, textures, diagrams, OG cards, or placeholders during development
- stop trusting a generator that keeps "succeeding" while producing broken files

Skip it when the asset should be vector/HTML (logos, icons, diagrams you can hand-code) — code beats a diffusion model for anything with exact geometry or text.

## 1. Pick the backend (cheapest working route first)

Decide from what the environment actually has, not from preference.

| Situation | Route | Notes |
|---|---|---|
| Agent has an image tool/provider configured | Use it directly | Fastest, handles delivery |
| `OPENAI_API_KEY`/compatible key present | OpenAI-compatible images API | Script in this skill covers it |
| `FAL_KEY`/`REPLICATE_API_TOKEN` present | Hosted API via its CLI or HTTP | Check its CLI first |
| Local GPU, free/unlimited needed | ComfyUI / local diffusion | No text fidelity; slow first run |
| Only a chat UI logged in | UI automation | Last resort — brittle, state-dependent |
| Nothing available | Say so, don't fabricate | Report the blocker |

Probe before committing, and print what you found:

```bash
env | grep -Ei 'OPENAI|FAL|REPLICATE|ANTHROPIC' | sed 's/=.*/=<set>/'
command -v comfy fal replicate codex 2>/dev/null
```

Pick the route whose prerequisites you actually confirmed. Do not assume.

## 2. Write the prompt as a build spec

Emit the prompt as labelled fields, not prose. Incomplete specs produce generic output.

```text
subject:    <exact thing depicted>
role:       <asset type: hero, icon, OG card, diagram, texture, portrait>
style:      <design language>
palette:    <2-4 named colours, tied to existing brand tokens if any>
composition:<framing, negative space, focal placement>
lighting:   <material/light notes>
constraints:<no text, no watermark, aspect ratio, background>
```

Hard rules:

- **Never let the model render critical text.** Generate text-free art and overlay exact text in HTML/SVG/Pillow/canvas. Model text gets misspelled.
- Put the aspect ratio and "no text" in every prompt; they are the two most violated constraints.
- For diagrams and infographics, describe the *structure* (nodes, arrows, layers), not the mood; if the output is only vaguely on-theme, regenerate once with a stricter spec and then stop and say so.
- Reuse the project's palette. Inspect existing CSS/tokens before prompting — do not invent a new colour language per image.

## 3. Generate

Any of these are acceptable; the skill's script picks automatically:

```bash
# 1. Agent's own image tool, if configured — call it directly.

# 2. Backend-agnostic script (this skill):
python scripts/generate_image.py --prompt "<full spec>" --out ./assets/hero.png --size 1536x1024

# 3. Explicit command template for anything else:
IMAGE_BACKEND_CMD='comfy-cli gen --prompt {prompt} --out {out}' python scripts/generate_image.py --prompt "..." --out hero.png
```

Keep one scratch dir per task and name outputs deterministically (`<slug>-<variant>.png`), so reruns overwrite rather than pile up.

## 4. Verify — always, before anything else

Run the checker. It parses real file headers and measures pixel content without assuming the generator told the truth:

```bash
python scripts/verify_image.py ./assets/hero.png
```

It reports format, dimensions, byte size, and a blank/uniform-frame verdict. Exit code 0 = usable, 1 = reject.

Reject and retry when it reports any of:

- not a real raster (HTML error page, 0 bytes, wrong magic)
- single-colour frame (usually a failed render)
- absurd dimensions (1x1, or far off the requested aspect)

If a vision-capable model is available, **also look at the image** and check it depicts the brief — the script proves the file is real, not that it is right. If you cannot see images, say so explicitly rather than claiming it matches.

## 5. Place and deliver

- Copy into the project, not a cache dir: `public/images/`, `assets/`, `src/assets/`, `public/og/`. Stable names like `logo-mark.svg`, `hero-cyber-command.png`, `og-home.png`.
- Make derivative sizes from the master file (`sips -z`, ImageMagick), never regenerate independently.
- Convert photographic art to WebP/JPEG before shipping; strip multi-megabyte PNGs from production paths.
- Chat delivery: attach the file itself (Hermes: `MEDIA:/absolute/path.png`). Never describe an image you didn't attach.

## 6. Anti-slop checklist

Reject your own output if it has:

- gradient-heavy "AI" look, glassmorphism, or fake glossy dashboards
- stock-photo corporate people, fake humans, cinematic filler
- emoji used as icons; generic rounded-pill UI; images trapped in rounded cards
- decorative imagery with no mapping to the actual subject matter
- garbled or misspelled rendered text
- a palette that contradicts the project's brand tokens

Prefer: high-contrast, blocky/technical type, solid surfaces, real subject matter, negative space reserved for copy, and imagery that maps to the exact concept being communicated.

## References

- `references/backend-matrix.md` — per-backend invocation details, env vars, and failure signatures.
- `references/hermes-routing.md` — Hermes-only shortcuts: native tool, Codex provider probe, config, delivery, UI-automation pitfalls.
- `references/project-asset-recipes.md` — shipping generated images inside a software project: where to save, derivatives, wiring, logo rules, scroll-scrub sequences.
- `scripts/generate_image.py` — routes to whatever backend is configured; prints JSON.
- `scripts/verify_image.py` — dependency-free raster/blankness checker.
