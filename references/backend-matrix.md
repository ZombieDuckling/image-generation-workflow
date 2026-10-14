# Backend matrix

Order of preference: the agent's own configured image tool, then a hosted API you
hold a key for, then local/free generation, then UI automation. Probe before choosing.

## Probe

```bash
env | grep -Ei 'OPENAI|IMAGE_|FAL|REPLICATE' | sed 's/=.*/=<set>/'
command -v comfy fal replicate codex curl 2>/dev/null
```

## 1. OpenAI-compatible images API

Works against any endpoint implementing `POST /images/generations`
(`b64_json` or `url` in `data[0]`).

```bash
export IMAGE_API_KEY=...            # or OPENAI_API_KEY
# export IMAGE_BASE_URL=https://api.openai.com/v1   # or a self-hosted/compatible gateway
# export IMAGE_MODEL=gpt-image-1
python scripts/generate_image.py --prompt "<spec>" --out hero.png --size 1536x1024
```

Failure signatures: 401 = key missing/invalid; 404 = wrong `IMAGE_BASE_URL` or model name;
`response had no b64_json or url` = the gateway ignored `response_format`; try
`IMAGE_B64=0` to get URLs instead. Some gateways cap sizes — 1024x1024 is safest.

## 2. Generic CLI / local backend

Anything that renders from a prompt on the command line fits the template slot:

```bash
IMAGE_BACKEND_CMD='comfy-cli gen --prompt {prompt} --out {out}' \
  python scripts/generate_image.py --prompt "<spec>" --out hero.png

# stable-diffusion.cpp, sdcpp, or a wrapper script:
IMAGE_BACKEND_CMD='sd --prompt {prompt} -o {out} -W 1024 -H 1024' \
  python scripts/generate_image.py --prompt "<spec>" --out hero.png
```

Local models: expect the first run to download multi-GB weights; text fidelity is poor,
so overlay text in code. Batch size >1 and fixed seeds help reproducibility.

## 3. Hosted API via vendor CLI

FAL/Replicate style:

```bash
fal run <model> --prompt "<spec>" --output hero.png     # if the fal CLI is installed
curl -s -X POST https://api.replicate.com/v1/predictions \
  -H "Authorization: Token $REPLICATE_API_TOKEN" -H 'Content-Type: application/json' \
  -d '{"input":{"prompt":"<spec>"}}'
```

Async providers return a job id, not an image — poll the status URL until the output
URL appears, download it, then run `verify_image.py`. A job id is not an image.

## 4. UI automation (last resort)

Only when no key exists and a logged-in chat UI is the sole path. Expect: login walls,
download dialogs, and latency. Rules: verify one small image end-to-end before batching;
never click password/payment/2FA dialogs — stop and ask the human.

## Failure signatures to watch for

| Symptom | Cause |
|---|---|
| File exists, 0 bytes | backend wrote nothing; treat as failure |
| File is HTML | saved an error page — check magic bytes, not size |
| Uniform colour frame | render failed after a valid request |
| Dimensions far off request | gateway ignoring size; clamp to a supported size |
| `verify_image.py` exit 1 | reject and regenerate once, then report honestly |

Any of these means the run failed regardless of what the generator returned.
