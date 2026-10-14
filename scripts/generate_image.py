#!/usr/bin/env python3
"""Backend-agnostic image generation entry point for any agent.

Route order:
  1. IMAGE_BACKEND_CMD env var - shell template with {prompt} {out} {size}
  2. OPENAI_API_KEY / IMAGE_API_KEY (+ optional IMAGE_BASE_URL, IMAGE_MODEL)
  3. hard error naming what to set

Usage:
  python generate_image.py --prompt "<spec>" --out out.png --size 1024x1024

Output is one JSON line: {"ok": true, "path": ..., "backend": ...}
Exit 0 on success, 1 on failure. Never trusts the backend's own claim:
the file is re-opened and size-checked before reporting ok.
"""
import argparse, base64, json, os, shlex, subprocess, sys, urllib.request


def gen_via_cmd(prompt, out, size):
    tpl = os.environ["IMAGE_BACKEND_CMD"]
    cmd = (tpl.replace("{prompt}", shlex.quote(prompt))
              .replace("{out}", shlex.quote(out))
              .replace("{size}", shlex.quote(size)))
    subprocess.run(cmd, shell=True, check=True)
    return "cmd:" + cmd.split()[0]


def gen_via_api(prompt, out, size):
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("IMAGE_API_KEY")
    if not key:
        raise RuntimeError("no OPENAI_API_KEY/IMAGE_API_KEY")
    base = os.environ.get("IMAGE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("IMAGE_MODEL", "gpt-image-1")
    body = {"model": model, "prompt": prompt, "n": 1, "size": size}
    if os.environ.get("IMAGE_B64", "1") == "1":
        body["response_format"] = "b64_json"
    req = urllib.request.Request(
        base + "/images/generations",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        data = json.load(r)
    item = (data.get("data") or [{}])[0]
    if item.get("b64_json"):
        with open(out, "wb") as f:
            f.write(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=600) as r:
            with open(out, "wb") as f:
                f.write(r.read())
    else:
        raise RuntimeError("response had no b64_json or url: " + str(list(item))[:200])
    return "openai-compatible:" + model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1024x1024")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    errors = []
    backend = None
    if os.environ.get("IMAGE_BACKEND_CMD"):
        try:
            backend = gen_via_cmd(a.prompt, a.out, a.size)
        except Exception as e:
            errors.append("cmd backend failed: %s" % e)
    if backend is None:
        try:
            backend = gen_via_api(a.prompt, a.out, a.size)
        except Exception as e:
            errors.append("api backend failed: %s" % e)

    if backend is None:
        print(json.dumps({"ok": False, "error": "; ".join(errors) or "no backend configured",
                          "hint": "set IMAGE_BACKEND_CMD, or OPENAI_API_KEY/IMAGE_API_KEY"}))
        return 1

    if not os.path.exists(a.out) or os.path.getsize(a.out) == 0:
        print(json.dumps({"ok": False, "backend": backend,
                          "error": "backend reported success but wrote no bytes to " + a.out}))
        return 1

    print(json.dumps({"ok": True, "backend": backend, "path": os.path.abspath(a.out),
                      "bytes": os.path.getsize(a.out),
                      "next": "run verify_image.py on this path before using it"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
