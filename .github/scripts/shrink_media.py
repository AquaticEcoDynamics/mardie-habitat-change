"""Shrink oversized images in the Static Web Apps copy of the site.

Figures are exported much larger than the book displays them (PNGs up to
~12,000 px wide, animated GIFs up to 3,600 px), which pushes the site past the
500 MB Static Web Apps limit. Images are shrunk in place under the same file
names, so no HTML needs changing:

- PNGs over PNG_MAX_PX on the long side are resized and re-encoded losslessly.
- GIFs are fitted within GIF_MAX_PX and recompressed with gifsicle --lossy.

A file is only replaced if the result is smaller. Run this on the SWA copy
only; GitHub Pages and the repo keep the originals. Needs Pillow and gifsicle.

Usage: python shrink_media.py <site_dir>
"""

import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

PNG_MAX_PX = 2400
GIF_MAX_PX = 1600
GIF_LOSSY = 60
SWA_LIMIT_MB = 500


def shrink(path):
    tmp = path + ".tmp"
    if path.lower().endswith(".png"):
        with Image.open(path) as im:
            if max(im.size) <= PNG_MAX_PX:
                return path, 0, 0
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            im.thumbnail((PNG_MAX_PX, PNG_MAX_PX), Image.LANCZOS)
            im.save(tmp, format="PNG", optimize=True)
    else:
        subprocess.run(
            ["gifsicle", "-O3", f"--lossy={GIF_LOSSY}", "--colors", "256",
             "--resize-fit", f"{GIF_MAX_PX}x{GIF_MAX_PX}", path, "-o", tmp],
            check=True,
        )
    before, after = os.path.getsize(path), os.path.getsize(tmp)
    if after < before:
        os.replace(tmp, path)
        return path, before, after
    os.remove(tmp)
    return path, 0, 0


if __name__ == "__main__":
    root = sys.argv[1]
    images = [
        os.path.join(dirpath, name)
        for dirpath, _, files in os.walk(root)
        for name in files
        if name.lower().endswith((".png", ".gif"))
    ]

    saved_bytes = 0
    with ProcessPoolExecutor() as pool:
        for path, before, after in pool.map(shrink, images):
            if before:
                print(f"shrunk {os.path.relpath(path, root)} "
                      f"({before / 1048576:.1f} -> {after / 1048576:.1f} MB)")
                saved_bytes += before - after

    site_mb = sum(
        os.path.getsize(os.path.join(dirpath, name))
        for dirpath, _, files in os.walk(root)
        for name in files
    ) / 1048576
    print(f"saved {saved_bytes / 1048576:.1f} MB, site is now {site_mb:.1f} MB")
    if site_mb > SWA_LIMIT_MB:
        print(f"::error::Site is {site_mb:.0f} MB, over the {SWA_LIMIT_MB} MB Static Web Apps limit")
        sys.exit(1)
    if site_mb > SWA_LIMIT_MB * 0.9:
        print(f"::warning::Site is {site_mb:.0f} MB, close to the {SWA_LIMIT_MB} MB Static Web Apps limit")
