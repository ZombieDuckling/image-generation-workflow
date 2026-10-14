# image-generation-workflow

An agent-agnostic skill for generating images and — more importantly — **verifying** them.

Works with any agent that can run shell commands or plain HTTP calls: Claude Code, Codex, Cursor, Hermes, or a bare script. No framework-specific tooling is assumed.

## Why

Image generators routinely return `success: true` while writing a blank frame, a truncated file, or an HTML error page. This skill's core rule:

> Never report success from the generator's own return value. Success = a verified raster at a known path.

The verification step is a real check, not a vibe: it parses file headers, measures pixel content, and fails loudly.

## Contents

- `SKILL.md` — the workflow: backend routing, prompt spec format, generation, verification, placement/delivery, anti-slop checklist.
- `scripts/generate_image.py` — routes to whichever backend is configured (`IMAGE_BACKEND_CMD`, or an OpenAI-compatible images API via `IMAGE_API_KEY`/`IMAGE_BASE_URL`/`IMAGE_MODEL`). Prints one JSON line; re-opens the file before claiming success.
- `scripts/verify_image.py` — dependency-free checker for PNG/JPEG/GIF/WEBP: format, dimensions, byte size, blank-frame detection. No PIL required (PNG content is decompressed with stdlib `zlib`). Exit 0 = usable, 1 = reject.
- `references/backend-matrix.md` — per-backend invocation, env vars, failure signatures.
- `references/hermes-routing.md` — Hermes-specific shortcuts (native tool, Codex provider probe, config, delivery).
- `references/project-asset-recipes.md` — shipping images inside a software project: paths, derivatives, wiring, logo rules, scroll-scrub sequences.

## Install

Copy the directory into whatever skills location your agent uses:

```bash
# Hermes
cp -R image-generation-workflow ~/.hermes/skills/creative/

# Claude Code / generic agents: point your skill loader at the directory,
# or paste SKILL.md into the agent's context and treat scripts/ as tools.
```

## Usage

```bash
# Generate (backend chosen from your environment)
export IMAGE_API_KEY=...           # or OPENAI_API_KEY
python scripts/generate_image.py --prompt "<full build spec>" --out hero.png --size 1536x1024
# {"ok": true, "backend": "openai-compatible:gpt-image-1", "path": "...", "bytes": 1234567, "next": "run verify_image.py on this path before using it"}

# Verify — always
python scripts/verify_image.py hero.png
# {"ok": true, "format": "png", "dimensions": "1536x1024", "aspect": 1.5, "bytes": 1234567, "content": "stdev=48.20"}
```

Rejected cases return exit 1 with reasons:

```json
{"ok": false, "format": "png", "dimensions": "1x1", "bytes": 69, "content": "stdev=0.00",
 "reject_reasons": ["implausibly small: 1x1", "only 69 bytes", "single-colour/uniform frame (pixel stdev 0.00) - likely failed render"]}
```

Also rejected: non-raster garbage (HTML saved as `.png`), zero-byte files, and backends that report success while writing nothing.

## Prompt spec format

Emit prompts as labelled fields, not prose:

```text
subject:     <exact thing depicted>
role:        <asset type: hero, icon, OG card, diagram, texture, portrait>
style:       <design language>
palette:     <2-4 named colours, tied to existing brand tokens if any>
composition: <framing, negative space, focal placement>
lighting:    <material/light notes>
constraints: <no text, no watermark, aspect ratio, background>
```

Two constraints are violated most often and belong in every prompt: the aspect ratio, and `no text`. Never let a model render critical text — overlay it in code.

## Licence

MIT — see `LICENSE`.
