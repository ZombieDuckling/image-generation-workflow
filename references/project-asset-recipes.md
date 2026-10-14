# Project asset recipes (folded in from dev-asset-generation)

Use when the image is destined for a software project rather than a chat reply.

## Decision matrix

| Need | Artifact | Method | Verification |
|---|---|---|---|
| Logo mark | SVG + PNG export | Hand-code SVG | Render at 32/128/512px |
| Wordmark | SVG/CSS text | Code, never AI text | Check exact spelling |
| Favicon | SVG + PNG/ICO | Derive from mark | Loads in tab |
| App icon | 1024 PNG + sizes | SVG base or AI mascot | Rounded-mask crop check |
| Hero image | PNG/WebP | AI generation | Inspect at target aspect |
| OG card | 1200x630 PNG | HTML/SVG template + AI bg, text overlaid | Preview size |
| Empty state | SVG/PNG | Simple SVG or AI | Renders in component |
| Texture/background | WebP/PNG | AI or CSS | File size acceptable |

## Where to save

- Vite/Next/static: `public/assets/`, `public/images/`, `public/logos/`, `public/icons/`
- React local: `src/assets/`; Electron: `assets/`, `build/icons/`
- Icons: `public/icon.png`, `public/favicon.svg`, `public/favicon.ico`, `build/icon.icns`
- OG: `public/og.png` or `public/og/<slug>.png`

Descriptive names: `logo-mark.svg`, `logo-horizontal.svg`, `app-icon-1024.png`, `hero-cyber-command.png`, `og-home.png`, `empty-state-no-projects.svg`.

## Derivatives from the master file

```bash
mkdir -p public/icons
sips -z 512 512 app-icon-1024.png --out public/icons/icon-512.png
sips -z 192 192 app-icon-1024.png --out public/icons/icon-192.png
sips -z 32 32 app-icon-1024.png --out public/favicon-32.png
```

If SVG→PNG is needed and no renderer exists, use a browser screenshot or `qlmanage`/`rsvg-convert` when installed.

## Wiring

- Update `img src`, CSS `background-image`, manifest icon path, OG metadata, or component imports.
- Logos need `alt` text; decorative images use `alt=""` or CSS background.
- Use WebP/JPEG for photographic art; do not ship multi-megabyte PNGs.

## Logo rules

1. Vector first — a logo starts as SVG, not PNG.
2. Simple geometry; it must read at 16–32px.
3. Never let AI draw the letters; use SVG paths or overlaid text.
4. Ship variants: mark-only, horizontal lockup, monochrome, favicon.
5. If it fails at 32px, simplify.
6. Keep the source editable; do not ship only a flattened raster.

## Prompt recipes

```text
Logo mark:  Minimal vector logo mark concept for <project>, <symbol>, geometric, strong silhouette, single-colour friendly, no text, centered, works as app icon, high contrast.
Hero:       Text-free hero image for <project>, <audience>, showing <scene>. Style <x>. Palette <y>. Composition leaving <left/right> negative space for copy. Lighting/material <z>. Constraints: no text, no watermark, production-grade, 16:9.
App icon:   Square app icon for <app>, centered <mascot>, simple strong silhouette, soft depth, <palette>, rounded-square safe composition, no text, recognizable at small sizes, 1024x1024.
OG card:    Abstract background for an OG preview card for <product>, <style>, high contrast, clean space for a large title, no text, no logo, 1200x630.
```

## Scroll-scrubbed motion sequences

If the page must feel like motion through a story:

1. Generate matching start and end frames (same angle, scale, lighting, composition).
2. Produce in-betweens with video/interpolation tooling (Runway/Pika/Kling/ComfyUI video nodes/RIFE/FramePack) or render a short clip and extract frames.
3. Export 40–120 numbered WebP/JPEG frames (`public/sequence/wash-0001.webp`).
4. Preload the first few; lazy-load the rest.
5. Map scroll progress to frame index; render to canvas or swap an `<img>` src.
6. Pin the section 200–500vh and place copy beats at progress thresholds.
7. Honour `prefers-reduced-motion` with a static key frame.

Hard rule: plumbing that *should* work is not proof. Open the rendered page and confirm visible motion, or say it is not done.

## Pitfalls

1. AI-rendered text gets misspelled — overlay exact text.
2. Saving assets only to a cache dir — move them into the project.
3. Skipping small-size logo checks.
4. Using PNG where SVG belongs.
5. Shipping oversized hero PNGs.
6. Ignoring the existing palette/components.
7. Not checking model/licence terms before commercial use.
8. Over-polishing placeholders while the build is blocked.
9. AI-slop layout tropes: big images trapped in rounded cards with gradients. Prefer full-bleed, editorial cuts, intentional sequencing.
10. Losing the domain: if the brief changes from lifestyle to industrial, regenerate assets for the new domain instead of re-labelling the old ones.
