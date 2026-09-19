"""Batch-extract flattened tvOS icons from local IPAs into icons/<bundleId>.png.

Pipeline (all existing OSS, no Apple toolchain needed):
  1. read Assets.car from each IPA
  2. decode renditions with car-unpacker-py (pure Python, Linux-clean)
     https://github.com/xiongnemo/car-unpacker-py  (+ lzfse binary it needs)
  3. keep icon-stack layers only, order Back -> Middle -> Front,
     composite onto one canvas, save as icons/<bundleId>.png

Known exceptions (decoded with macOS system CoreUI instead, same
400x240 'App Icon' rendition, verified pixel-identical in spirit
against App Store art where available):
  DearReader (com.localno12.losswords7),
  SolitairePants (com.mtvn.spongebobsolisquarepants)
Their catalogs (>1000 renditions) trip the traversal in car-unpacker-py.

Usage:
  python extract_icons.py <ipa_dir> [--car-unpacker car_unpacker.py] [--out icons]

 Icon-stack ordering rules (bottom -> top), verified against samples:
  explicit Back/Middle/Front in name  >  "(N)" suffix (plain = 0)
                                      >  LayerN / Layer-N (N-1)
                                      >  opaque-first, catalog order
"""
import csv
import glob
import os
import re
import subprocess
import sys
import zipfile

from PIL import Image

ICON_HINTS = ("icon", "tvos", "tvarcade", "tvapp", "appletv", "arcade")
JUNK_HINTS = ("topshelf", "shelf", "banner", "logo", "subtitle")


def layer_role(path, opaque):
    base = os.path.basename(path)
    low = base.lower()
    if "back" in low:
        return 0
    if "middle" in low:
        return 1
    if "front" in low:
        return 2
    # Opaque layers are the background even when Apple numbered the
    # character as Layer-0 (Amazing Bomberman, Little Orpheus, ...).
    if opaque:
        return -50
    m = re.search(r"\((\d+)\)", base)
    if m:
        return int(m.group(1))
    m = re.search(r"[Ll]ayer[-_ ]?(\d+)", base)
    if m:
        return int(m.group(1)) - 1
    return 99


def is_opaque(im):
    px = im.load()
    w, h = im.size
    step = max(1, min(w, h) // 60)
    for x in range(0, w, step):
        for y in range(0, h, step):
            if px[x, y][3] < 128:
                return False
    return True


def flatten(layers, dest):
    """Composite one icon variant (same stack) into a single PNG."""
    imgs = [Image.open(p).convert("RGBA") for p in layers]
    keyed = sorted(
        ((layer_role(p, is_opaque(im)), i, im)
         for i, (p, im) in enumerate(zip(layers, imgs))),
        key=lambda t: (t[0], t[1]),
    )
    ordered = [im for _, _, im in keyed]
    w = max(im.size[0] for im in ordered)
    h = max(im.size[1] for im in ordered)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for im in ordered:
        canvas = Image.alpha_composite(canvas, _centered(canvas.size, im))
    canvas.save(dest)
    return [os.path.basename(p) for p in layers]


def _centered(size, im):
    if im.size == size:
        return im
    bg = Image.new("RGBA", size, (0, 0, 0, 0))
    bg.paste(im, ((size[0] - im.size[0]) // 2,
                  (size[1] - im.size[1]) // 2), im)
    return bg


def icon_layers(files):
    usable = []
    for f in files:
        try:
            st = Image.open(f).size
        except Exception:
            continue
        if st[0] < 8 or st[1] < 8:
            continue
        usable.append(f)
    files = usable or files
    icon_named = [f for f in files
                  if "icon" in os.path.basename(f).lower()]
    pool = icon_named or files
    kept = [f for f in pool
            if any(h in os.path.basename(f).lower() for h in ICON_HINTS)
            and not any(j in os.path.basename(f).lower() for j in JUNK_HINTS)]
    return kept or pool


def variant_groups(layers):
    """Group by exact canvas size. tvOS small icons are 400x240;
    truncated 400xN slices and TopShelf banners must not mix in."""
    groups = {}
    for p in layers:
        groups.setdefault(Image.open(p).size, []).append(p)
    return groups


def pick_group(groups):
    if (400, 240) in groups:
        return groups[(400, 240)]
    w400 = {s: v for s, v in groups.items() if s[0] == 400}
    if w400:
        return w400[max(w400, key=lambda s: s[1])]
    return groups[max(groups, key=lambda s: s[0] * s[1])]


def extract_one(ipa_path, bundle_id, car_unpacker, workdir, outdir):
    with zipfile.ZipFile(ipa_path) as z:
        cars = [n for n in z.namelist() if n.endswith("/Assets.car")]
        # Prefer the top-level Payload/<App>.app/Assets.car; nested ones
        # (frameworks, bundles) hold content art, not the app icon.
        top = [c for c in cars if len(c.split("/")) == 3]
        car_name = (top or cars or [None])[0]
        if car_name is None:
            return "no Assets.car"
        car_path = os.path.join(workdir, bundle_id + ".car")
        with open(car_path, "wb") as f:
            f.write(z.read(car_name))
    raw = os.path.join(workdir, bundle_id)
    subprocess.run([sys.executable, car_unpacker, car_path, raw],
                   capture_output=True, timeout=600, check=False)
    files = [f for f in glob.glob(os.path.join(raw, "*.png"))]
    if not files:
        return "decoder wrote nothing"
    layers = icon_layers(files)
    groups = variant_groups(layers)
    best = pick_group(groups)  # 400-wide icon group wins over banners
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, bundle_id + ".png")
    used = flatten(best, dest)
    got = Image.open(dest).size
    if got != (400, 240):
        return f"SIZE-WARN {got}: " + ", ".join(u[:50] for u in used)
    return "ok: " + ", ".join(u[:50] for u in used)


def main():
    ipa_dir = sys.argv[1]
    car_unpacker = sys.argv[2] if len(sys.argv) > 2 else "car_unpacker.py"
    outdir = sys.argv[3] if len(sys.argv) > 3 else "icons"
    workdir = sys.argv[4] if len(sys.argv) > 4 else ".work-icons"
    os.makedirs(workdir, exist_ok=True)

    with open("bundleId.csv") as f:
        ids = {r["name"]: r["bundleId"] for r in csv.DictReader(f)}

    ok, failed = 0, []
    for ipa in sorted(glob.glob(os.path.join(ipa_dir, "*.ipa"))):
        app = os.path.basename(ipa)[:-4].rsplit("_", 1)[0]
        bid = ids.get(app)
        if not bid:
            failed.append((app, "not in bundleId.csv"))
            continue
        if os.path.exists(os.path.join(outdir, bid + ".png")):
            ok += 1
            continue
        try:
            res = extract_one(ipa, bid, car_unpacker, workdir, outdir)
        except Exception as e:  # noqa: BLE001 - batch must continue
            res = f"error: {e!r}"
        print(f"{app}: {res}", flush=True)
        if res.startswith("ok"):
            ok += 1
        else:
            failed.append((app, res))
    print(f"\ndone: {ok} ok, {len(failed)} failed")
    for app, reason in failed:
        print(f"  FAIL {app}: {reason}")


if __name__ == "__main__":
    main()
