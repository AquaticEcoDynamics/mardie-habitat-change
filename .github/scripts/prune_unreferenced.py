"""Copy the rendered site, dropping files that no page links to.

Azure Static Web Apps caps a deployment at 500 MB, and docs/ carries old
animations and images that are no longer used by any chapter. A file is kept
if its name (raw or URL-encoded) appears in any HTML/JS/CSS/JSON file, or if
it is itself one of those text assets. Matching is by file name only, so it
errs on the side of keeping things.

Usage: python prune_unreferenced.py <src_dir> <dest_dir>
"""

import os
import shutil
import sys
import urllib.parse

TEXT_EXT = {".html", ".htm", ".css", ".js", ".json", ".xml", ".txt", ".ico"}

src, dest = sys.argv[1], sys.argv[2]

corpus = []
for dirpath, _, files in os.walk(src):
    for name in files:
        if os.path.splitext(name)[1].lower() in TEXT_EXT:
            with open(os.path.join(dirpath, name), encoding="utf-8", errors="ignore") as fh:
                corpus.append(fh.read())
corpus = "\n".join(corpus)

kept_bytes = dropped_bytes = 0
for dirpath, _, files in os.walk(src):
    for name in files:
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, src)
        size = os.path.getsize(path)
        keep = (
            os.path.splitext(name)[1].lower() in TEXT_EXT
            or rel.startswith("site_libs" + os.sep)
            or name in corpus
            or urllib.parse.quote(name) in corpus
        )
        if keep:
            os.makedirs(os.path.join(dest, os.path.dirname(rel)), exist_ok=True)
            shutil.copy2(path, os.path.join(dest, rel))
            kept_bytes += size
        else:
            print(f"skipping unreferenced {rel} ({size / 1048576:.1f} MB)")
            dropped_bytes += size

print(f"kept {kept_bytes / 1048576:.1f} MB, skipped {dropped_bytes / 1048576:.1f} MB")
