# Hermes routing notes (folded in from hermes-image-generation-routing)

These are Hermes-specific shortcuts. Ignore this file if you are a different agent.

## Prefer the native path

1. Use Hermes's built-in `image_generate` tool first when configured — it returns a path or URL and handles chat delivery.
2. If the configured provider is unavailable (e.g. FAL selected with no `FAL_KEY`), **do not stop at "image generation unavailable"** — check for bundled providers under `plugins/image_gen/`.
3. With ChatGPT/Codex OAuth available, the bundled `openai-codex` provider is preferred over driving chatgpt.com in a browser: it needs no API key, writes PNGs under `$HERMES_HOME/cache/images/`, and is far more reliable than GUI automation.

## Direct provider probe (when the tool is unavailable)

```bash
HERMES="${HERMES_HOME:-$HOME/.hermes}/hermes-agent"
"$HERMES/venv/bin/python" - <<PY
import os, sys, json
from importlib.util import spec_from_file_location, module_from_spec
repo = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")) + "/hermes-agent"
sys.path.insert(0, repo)
p = repo + "/plugins/image_gen/openai-codex/__init__.py"
spec = spec_from_file_location('openai_codex_image_gen', p)
mod = module_from_spec(spec); spec.loader.exec_module(mod)
provider = mod.OpenAICodexImageGenProvider()
print('available', provider.is_available())
print(json.dumps(provider.generate('A polished text-free mascot image', aspect_ratio='square'), indent=2))
PY
```

If it returns success, send the returned path with `MEDIA:/absolute/path.png`, then still run `scripts/verify_image.py` on it.

## Configure Hermes to prefer it persistently

```bash
hermes config set image_gen.provider openai-codex
hermes config set image_gen.model gpt-image-2-medium
```

Restart the gateway/session after config changes. `gpt-image-2-low` for fast iteration, `-medium` for default chat quality, `-high` for maximum fidelity.

## Local/free vs hosted quality

- Hosted/GPT models win on prompt adherence, readable text, complex scenes, faces, editing.
- Local ComfyUI wins on cost, privacy, offline, stylised art, backgrounds, avatars — but expect garbled text, so overlay text in code.

## UI automation pitfalls

Only when a native provider cannot do the job:

- macOS computer-use needs `cua-driver`: `hermes computer-use install`; permissions for **CuaDriver.app** (Accessibility + Screen Recording) via `hermes computer-use permissions status|grant` and `hermes computer-use doctor`.
- Never click password, payment, 2FA, or permission dialogs — stop and ask the human.
- Browser UI state, login prompts, and downloads make this the least reliable route; verify one image end-to-end before batching.

## Delivery

Verify the file exists and is a real raster, then attach it:

```text
MEDIA:/absolute/path/generated.png
```
