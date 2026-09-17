#!/usr/bin/env python3
"""Regenerate palette_list/manifest.json from the palette PNGs in this folder.

Run this every time you add or remove a file here:

    python3 palette_list/build_manifest.py

The app only shows palettes that are listed in manifest.json, and manifest.json only
lists what's currently in this folder — so a palette disappears from the app the moment
its PNG is removed and this script is re-run. Nothing else needs to change.

Each PNG must be the standard lospec.com palette strip: a single row of N equal-width
square swatches (so width = N * height, e.g. a 12-color palette at 32x32 per swatch is
384x32). That's what "Export > PNG" on lospec.com produces.
"""
import glob
import json
import os
import re

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def base_name(name):
    base = os.path.splitext(name)[0]
    return re.sub(r'-\d+x$', '', base, flags=re.IGNORECASE)  # strip a trailing "-32x" swatch-size suffix


def label_from_filename(name):
    words = re.split(r'[-_]+', base_name(name))
    return ' '.join(w.capitalize() for w in words if w)


def key_from_filename(name):
    return re.sub(r'[^a-z0-9]+', '_', base_name(name).lower()).strip('_')


def extract_colors(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if h <= 0 or w % h != 0:
        raise ValueError(f'expected a strip of square swatches (width a multiple of height), got {w}x{h}')
    n = w // h
    colors = []
    for i in range(n):
        cx = i * h + h // 2
        cy = h // 2
        r, g, b = im.getpixel((cx, cy))
        colors.append('#%02x%02x%02x' % (r, g, b))
    return colors


def main():
    entries = []
    used_keys = set()
    for path in sorted(glob.glob(os.path.join(HERE, '*.png'))):
        name = os.path.basename(path)
        key = key_from_filename(name)
        if key in used_keys:
            i = 2
            while f'{key}_{i}' in used_keys:
                i += 1
            key = f'{key}_{i}'
        used_keys.add(key)
        try:
            colors = extract_colors(path)
        except Exception as e:
            print(f'Skipping {name}: {e}')
            continue
        if len(colors) < 2:
            print(f'Skipping {name}: only {len(colors)} distinct color(s) found')
            continue
        entries.append({
            'key': key,
            'label': label_from_filename(name),
            'file': name,
            'colors': colors,
        })

    manifest_path = os.path.join(HERE, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(entries, f, indent=2)
        f.write('\n')

    print(f'Wrote {manifest_path} with {len(entries)} palette(s):')
    for e in entries:
        print(f"  - {e['label']} ({len(e['colors'])} colors) <- {e['file']}")


if __name__ == '__main__':
    main()
