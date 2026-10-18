"""The film: every rendered shot, in story order, encoded shot by shot for the home page's opening.

    blender -b --factory-startup -P blender/film.py

Reads the frame folders blender/arrival.py and blender/lab.py wrote and encodes each shot on its
own, blender/out/film/<tier>/<shot>.mp4, for every tier the frames are big enough for:
  phone 1280 x 720, desk 1920 x 1080, hd 2560 x 1440 (from 4K frames).
The site plays the shots back to back (src/scripts/film.ts): Cloudflare serves files of up to
25 MiB, which one file of the whole film at a watchable bitrate is not, and the shots meet at hard
cuts, where the switch from one file to the next cannot be seen. From 4K frames it also writes the
whole film as one file, blender/out/film-master-4k.mp4, for sharing (not served by the site).
film.json records where each shot starts and ends in seconds, for the page's subtitles and sound.
-- --preview joins the quick preview frames (arrival.py --preview, lab.py --preview 1) into one
file, blender/out/film-preview.mp4, for checking the cut and the motion before the long render.
The film fades up from black and dips to black after the orbit (a change of world); otherwise it
cuts like a game's cinematic.
"""

import bpy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(
    sys.argv[sys.argv.index('-P') + 1] if '-P' in sys.argv else __file__)))
OUT = os.path.join(ROOT, 'blender', 'out')
FPS = 24
PREVIEW = '--preview' in sys.argv
SHOTS = [
    ('orbit', 'arrival/orbit'),
    ('descent', 'arrival/descent'),
    ('ramp', 'arrival/ramp'),
    ('street', 'arrival/street'),
    ('approach', 'arrival/approach'),
    ('door', 'arrival/door'),
    ('lab-enter', 'lab-enter'),
    ('lab-breaker', 'lab-breaker'),
    ('lab-power', 'lab-power'),
    ('lab-bench', 'lab-bench'),
]
if PREVIEW:
    # Where the previews are: arrival/preview/<shot> and preview/<lab shot>. The orbit has no
    # preview (nothing in it moves but the camera); its film frames stand in.
    SHOTS = [(n, rel if n == 'orbit' else (rel.replace('arrival/', 'arrival/preview/') if rel.startswith('arrival/')
                                            else f'preview/{rel}')) for n, rel in SHOTS]
FADE_IN, DIP = 18, 10  # frames
# Tier: (size, quality). A tier is made only when the frames are near that size or bigger (a
# little upscaling is invisible; a lot is not worth the bytes).
TIERS = {
    'phone': ((1280, 720), 'MEDIUM'),
    'desk': ((1920, 1080), 'HIGH'),
    'hd': ((2560, 1440), 'HIGH'),
}
LIMIT = 24 * 1024 * 1024  # under Cloudflare's 25 MiB per file


def frames(rel):
    d = os.path.join(OUT, rel)
    if not os.path.isdir(d):
        return d, []
    return d, sorted(f for f in os.listdir(d) if f[:4].isdigit() and f.endswith(('.png', '.jpg')))


def width_of(path):
    img = bpy.data.images.load(path, check_existing=False)
    w = img.size[0]
    bpy.data.images.remove(img)
    return w


def add_strip(se, name, d, files, channel, start):
    strips = se.strips if hasattr(se, 'strips') else se.sequences
    try:
        st = strips.new_image(name, os.path.join(d, files[0]), channel, start, fit_method='FIT')
    except TypeError:
        st = strips.new_image(name, os.path.join(d, files[0]), channel, start)
    for f in files[1:]:
        st.elements.append(f)
    return st


def fade(st, name, first, start, n):
    """Fades through black: up at the very start, and out of the orbit into the street."""
    keys = []
    if first:
        keys += [(start, 0.0), (start + FADE_IN, 1.0)]
    if name == 'orbit':
        keys += [(start + n - DIP, 1.0), (start + n - 1, 0.0)]
    if name == 'descent':
        keys += [(start, 0.0), (start + DIP, 1.0)]
    for frame, alpha in sorted(keys):
        st.blend_alpha = alpha
        st.keyframe_insert('blend_alpha', frame=frame)


def scene(res, label):
    sc = bpy.data.scenes.new(label)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.fps = FPS
    sc.view_settings.view_transform = 'Standard'  # the frames are already graded
    return sc


def encode(sc, path, quality, kbps=0):
    try:
        sc.render.image_settings.media_type = 'VIDEO'
    except (AttributeError, TypeError):
        pass
    sc.render.image_settings.file_format = 'FFMPEG'
    ff = sc.render.ffmpeg
    ff.format = 'MPEG4'
    ff.codec = 'H264'
    if kbps:
        ff.constant_rate_factor = 'NONE'
        ff.video_bitrate = kbps
        ff.maxrate = int(kbps * 1.3)
        ff.buffersize = kbps * 2
    else:
        ff.constant_rate_factor = quality
    ff.ffmpeg_preset = 'BEST'
    ff.gopsize = FPS
    ff.audio_codec = 'NONE'
    sc.render.use_sequencer = True
    sc.render.filepath = path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.render.render(animation=True, scene=sc.name)
    return os.path.getsize(path)


shots = []
for name, rel in SHOTS:
    d, files = frames(rel)
    if files:
        shots.append((name, d, files))
    else:
        print(f'[film] missing {rel}, skipped', flush=True)

if PREVIEW:
    sc = scene((960, 540), 'preview')
    se = sc.sequence_editor_create()
    at = 1
    for i, (name, d, files) in enumerate(shots):
        fade(add_strip(se, name, d, files, 1 + i % 2, at), name, i == 0, at, len(files))
        at += len(files)
    sc.frame_start, sc.frame_end = 1, at - 1
    size = encode(sc, os.path.join(OUT, 'film-preview.mp4'), 'MEDIUM')
    print(f'[film] film-preview.mp4 {size / 1e6:.1f} MB, {(at - 1) / FPS:.1f} s', flush=True)
    sys.exit(0)

src_w = min(width_of(os.path.join(d, files[0])) for _, d, files in shots)
tiers = [t for t, (res, _) in TIERS.items() if src_w >= res[0] * 0.8]

chapters, start = [], 0
for i, (name, d, files) in enumerate(shots):
    n = len(files)
    chapters.append({'id': name, 'start': round(start / FPS, 3), 'end': round((start + n) / FPS, 3)})
    start += n
    for tag in tiers:
        res, quality = TIERS[tag]
        sc = scene(res, f'{name}-{tag}')
        st = add_strip(sc.sequence_editor_create(), name, d, files, 1, 1)
        fade(st, name, i == 0, 1, n)
        sc.frame_start, sc.frame_end = 1, n
        path = os.path.join(OUT, 'film', tag, f'{name}.mp4')
        size = encode(sc, path, quality)
        if size > LIMIT:
            # Over the per-file limit: the highest bitrate that fits.
            size = encode(sc, path, quality, kbps=int(LIMIT * 8 / 1000 / (n / FPS) * 0.9))
        print(f'[film] {tag}/{name}.mp4 {size / 1e6:.1f} MB', flush=True)
        bpy.data.scenes.remove(sc)

if src_w >= 3840:
    # The 4K master, one file, for sharing.
    sc = scene((3840, 2160), 'master')
    se = sc.sequence_editor_create()
    at = 1
    for i, (name, d, files) in enumerate(shots):
        fade(add_strip(se, name, d, files, 1 + i % 2, at), name, i == 0, at, len(files))
        at += len(files)
    sc.frame_start, sc.frame_end = 1, at - 1
    size = encode(sc, os.path.join(OUT, 'film-master-4k.mp4'), 'PERC_LOSSLESS')
    print(f'[film] film-master-4k.mp4 {size / 1e6:.1f} MB', flush=True)

with open(os.path.join(OUT, 'film.json'), 'w', encoding='utf-8') as fh:
    json.dump({'fps': FPS, 'duration': chapters[-1]['end'] if chapters else 0, 'tiers': tiers,
               'chapters': chapters}, fh, indent=2)
print('[film] done', flush=True)
