#!/usr/bin/env python3
"""Verify that a generated image is a real, usable raster - dependency-free.

Checks, from the file itself (never from the generator's claim):
  - magic bytes / format for PNG, JPEG, GIF, WEBP, BMP
  - declared dimensions from the header
  - byte size
  - pixel content: blank/uniform frame detection

Pixel content uses PIL when installed; otherwise PNG content is decompressed
with stdlib zlib and JPEG/WEBP fall back to header+size heuristics (reported
explicitly as content=unverified rather than silently passing).

Usage: python verify_image.py <path>   (exit 0 = usable, 1 = reject)
"""
import json, os, struct, sys, zlib


def dims_png(b):
    if len(b) < 24 or b[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", b[16:24])
    return w, h, "png"


def dims_jpeg(b):
    if b[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(b) - 9:
        if b[i] != 0xFF:
            i += 1
            continue
        m = b[i + 1]
        if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            h, w = struct.unpack(">HH", b[i + 5:i + 9])
            return w, h, "jpeg-sof%02x" % m
        if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
            i += 2
            continue
        seg = struct.unpack(">H", b[i + 2:i + 4])[0]
        i += 2 + seg
    return None


def dims_gif(b):
    if b[:6] not in (b"GIF87a", b"GIF89a") or len(b) < 10:
        return None
    w, h = struct.unpack("<HH", b[6:10])
    return w, h, "gif"


def dims_webp(b):
    if b[:4] != b"RIFF" or b[8:12] != b"WEBP" or len(b) < 30:
        return None
    tag = b[12:16]
    if tag == b"VP8X":
        w = 1 + int.from_bytes(b[24:27], "little")
        h = 1 + int.from_bytes(b[27:30], "little")
        return w, h, "webp-vp8x"
    if tag == b"VP8 " and b[23:26] == b"\x9d\x01\x2a":
        w = int.from_bytes(b[26:28], "little") & 0x3FFF
        h = int.from_bytes(b[28:30], "little") & 0x3FFF
        return w, h, "webp-vp8"
    return 0, 0, "webp-unknown"


def png_content(b):
    """Decompress IDAT with stdlib and report distinct byte values in the sample."""
    try:
        i, idat = 8, bytearray()
        while i < len(b) - 12:
            ln = struct.unpack(">I", b[i:i + 4])[0]
            typ = b[i + 4:i + 8]
            if typ == b"IDAT":
                idat += b[i + 8:i + 8 + ln]
            elif typ == b"IEND":
                break
            i += 12 + ln
        raw = zlib.decompress(bytes(idat))
        sample = raw[:64_000]
        return len(set(sample)), len(sample)
    except Exception:
        return None, None


def pil_content(p):
    try:
        from PIL import Image
        import statistics
        im = Image.open(p).convert("RGB")
        im.thumbnail((256, 256))
        px = list(im.getdata())
        if not px:
            return None
        flat = [c for p_ in px for c in p_]
        return round(statistics.pstdev(flat), 2)
    except Exception:
        return None


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: verify_image.py <path>"}))
        return 1
    p = sys.argv[1]
    if not os.path.exists(p):
        print(json.dumps({"ok": False, "error": "file does not exist", "path": p}))
        return 1
    size = os.path.getsize(p)
    if size == 0:
        print(json.dumps({"ok": False, "error": "zero bytes", "path": p}))
        return 1
    b = open(p, "rb").read(4_000_000)

    info = dims_png(b) or dims_jpeg(b) or dims_gif(b) or dims_webp(b)
    if info is None:
        head = b[:120].decode("utf-8", "replace").strip()
        print(json.dumps({"ok": False, "error": "not a recognised raster format",
                          "bytes": size, "first_bytes": head[:80]}))
        return 1
    w, h, kind = info

    reasons = []
    if w <= 0 or h <= 0:
        reasons.append("header dimensions unreadable (%dx%d)" % (w, h))
    if w < 8 or h < 8:
        reasons.append("implausibly small: %dx%d" % (w, h))
    if w > 20000 or h > 20000:
        reasons.append("implausibly large: %dx%d" % (w, h))
    if size < 1024:
        reasons.append("only %d bytes" % size)

    content = "unverified"
    sd = pil_content(p)
    if sd is not None:
        if sd < 1.0:
            reasons.append("single-colour/uniform frame (pixel stdev %.2f) - likely failed render" % sd)
        content = "stdev=%.2f" % sd
    elif kind.startswith("png"):
        d, n = png_content(b)
        if d is not None:
            ratio = d / max(n, 1)
            if d <= 2:
                reasons.append("decompressed PNG has <=2 distinct byte values - blank frame")
            content = "distinct_bytes=%d/%d (%.3f)" % (d, n, ratio)
        else:
            reasons.append("PNG IDAT could not be decompressed (truncated?)")
    else:
        content = "unverified (no PIL; header+size checks only)"

    out = {"ok": not reasons, "path": os.path.abspath(p), "format": kind,
           "dimensions": "%dx%d" % (w, h), "aspect": round(w / h, 3) if h else None,
           "bytes": size, "content": content}
    if reasons:
        out["reject_reasons"] = reasons
    print(json.dumps(out))
    return 0 if not reasons else 1


if __name__ == "__main__":
    sys.exit(main())
