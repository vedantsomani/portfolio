"""Renders the final film on a shared multi-GPU server, politely.

    python3 blender/farm.py --blender ~/archive-render/blender/blender --gpus 1,2,3,6

From the repository root (a copy with blender/, blender/assets/ and the lab's inputs). In order:
  1. build   every shot is built at final quality, keyed, its simulation baked, and saved to
             blender/out/work/<shot>.blend (CPU, a few at a time);
  2. render  a queue of jobs, one per (shot, slice of its frames); each GPU takes the next job
             when it is free, and only while nobody else's work is on it. Frames already on disk
             are skipped, so the farm can be stopped and run again;
  3. film    blender/film.py encodes the shots for the site and the 4K master.
The stills (the lab hub at 4K, the close-ups) and the hologram loop are jobs in the same queue.
Each Blender runs at low priority with a capped thread count. Logs: blender/out/work/logs/.
--preview instead renders every shot quickly (960 x 540, few samples, no simulation) across the
GPUs and joins them into blender/out/film-preview.mp4, to check the cut and the motion first.
"""

import argparse
import concurrent.futures
import os
import queue
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'blender', 'out', 'work')
LOGS = os.path.join(WORK, 'logs')
ARRIVAL = ['orbit', 'descent', 'ramp', 'street', 'approach', 'door']
LAB = ['lab-enter', 'lab-breaker', 'lab-power', 'lab-bench', 'lab-reveal']

ap = argparse.ArgumentParser()
ap.add_argument('--blender', required=True)
ap.add_argument('--gpus', default='0')
ap.add_argument('--samples', type=int, default=1024)
ap.add_argument('--threads', type=int, default=16, help='CPU threads per render process')
ap.add_argument('--slices', type=int, default=0, help='jobs per shot (default: one per GPU)')
ap.add_argument('--only', default='', help='comma-separated shots (arrival names, lab)')
ap.add_argument('--skip', default='', help='stages to skip: build,render,stills,film')
ap.add_argument('--libs', default='', help='extra LD_LIBRARY_PATH for Blender')
ap.add_argument('--preview', action='store_true', help='quick frames of every shot, then one preview film')
ap.add_argument('--res', default='', help='render the film at WxH instead of as built (4K)')
ap.add_argument('--stills', default='hub,close,holo', help='which stills to render')
ap.add_argument('--hub-samples', default='4096')
ap.add_argument('--threshold', default='', help='adaptive noise threshold for this pass')
ap.add_argument('--volstep', default='', help='volume step rate for this pass')
ap.add_argument('--max', action='store_true', help='the uncompromised render settings')
ap.add_argument('--nodust', action='store_true', help='leave out the footstep dust and the motes')
ap.add_argument('--backend', default='', help='CUDA: CUDA before OptiX (faster on GPUs without RT cores)')
args = ap.parse_args()
GPUS = [int(g) for g in args.gpus.split(',')]  # a GPU listed twice runs two renders at once
SKIP = set(filter(None, args.skip.split(',')))
SHOTS = [s for s in ARRIVAL + LAB if not args.only or s in args.only.split(',')]
SLICES = args.slices or len(GPUS)
OVERRIDE = (['--res', args.res] if args.res else []) + ['--samples', str(args.samples)]
OVERRIDE += (['--threshold', args.threshold] if args.threshold else []) + (['--volstep', args.volstep] if args.volstep else [])
OVERRIDE += ['--max'] if args.max else []
NODUST_ARRIVAL = ['--nodust'] if args.nodust else []
NODUST_LAB = ['--nodust', '1'] if args.nodust else []
os.makedirs(LOGS, exist_ok=True)


def say(msg):
    print(time.strftime('%H:%M:%S'), msg, flush=True)


def env(gpu=None):
    e = dict(os.environ)
    if gpu is not None:
        e['CUDA_VISIBLE_DEVICES'] = str(gpu)
    if args.backend:
        e['ARCHIVE_GPU'] = args.backend
    if args.libs:
        e['LD_LIBRARY_PATH'] = args.libs + ':' + e.get('LD_LIBRARY_PATH', '')
    return e


def blender(script, opts, log, gpu=None, threads=None):
    cmd = ['nice', '-n', '10', args.blender, '-b', '--factory-startup', '-t', str(threads or args.threads),
           '-P', os.path.join(ROOT, 'blender', script), '--'] + opts
    with open(os.path.join(LOGS, log), 'a') as fh:
        fh.write(f'\n$ {" ".join(cmd)}\n')
        fh.flush()
        return subprocess.call(cmd, cwd=ROOT, env=env(gpu), stdout=fh, stderr=subprocess.STDOUT)


MINE = set(GPUS)  # GPUs this farm runs on: our own renders there are not someone else's work
STARTED = set()


def busy(gpu):
    """Someone else's work on this GPU (checked before our first job on it): memory in use, or the
    GPU working hard."""
    if gpu in STARTED:
        return False
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '-i', str(gpu), '--query-gpu=memory.used,utilization.gpu',
             '--format=csv,noheader,nounits'], text=True)
        mem, util = (float(v) for v in out.strip().split(','))
        return mem > 12000 or util > 40
    except (subprocess.SubprocessError, ValueError, OSError):
        return False


# 1. Build: every shot keyed and baked, a few at a time (the dust simulation takes many cores).
def build(shot):
    if shot in LAB:
        opts = ['--shots', shot, '--art', 'none', '--quality', 'ultra', '--samples', str(args.samples),
                '--stage', 'build']
        return blender('lab.py', opts, f'build-{shot}.log', threads=48)
    opts = ['--shot', shot, '--anim', '--quality', 'ultra', '--res', '3840x2160',
            '--samples', str(args.samples), '--stage', 'build']
    return blender('arrival.py', opts, f'build-{shot}.log', threads=48)


if args.preview:
    SKIP |= {'build', 'stills', 'render'}
    jobs = queue.Queue()
    for k in range(SLICES):
        for s in SHOTS:
            if s == 'orbit':
                continue  # nothing in it moves but the camera; the film's own frames stand in
            if s in LAB:
                jobs.put(('lab.py', ['--shots', s, '--art', 'none', '--samples', '12', '--scale', '0.5',
                                     '--preview', '1', '--slice', f'{k}/{SLICES}'], f'preview-{s}-{k}'))
            else:
                jobs.put(('arrival.py', ['--shot', s, '--anim', '--preview', '--res', '960x540',
                                         '--samples', '12', '--slice', f'{k}/{SLICES}'], f'preview-{s}-{k}'))

if 'build' not in SKIP:
    if 'door' in SHOTS:
        # The lab room the door shot looks into, before that shot is built.
        say('build lab room')
        if blender('lab.py', ['--shots', 'room', '--art', 'none'], 'build-lab-room.log', threads=48):
            sys.exit(f'lab room failed; see {LOGS}/build-lab-room.log')
    say(f'build {SHOTS}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        codes = dict(zip(SHOTS, pool.map(build, SHOTS)))
    for s, code in codes.items():
        say(f'built {s}: exit {code}')
    bad = [s for s, code in codes.items() if code]
    if bad:
        sys.exit(f'builds failed: {bad}; see {LOGS}/build-*.log')

# 2. Render: jobs per (shot, slice), plus the stills, taken by whichever GPU is free.
if not args.preview:
    jobs = queue.Queue()
if 'stills' not in SKIP:
    stills = args.stills.split(',')
    if 'hub' in stills:
        jobs.put(('lab.py', ['--shots', 'hub', '--art', 'none', '--quality', 'ultra', '--samples',
                             args.hub_samples], 'hub'))
    if 'close' in stills:
        jobs.put(('lab.py', ['--shots', 'close', '--art', 'none', '--quality', 'ultra', '--samples', '2048'], 'close'))
    if 'holo' in stills:
        jobs.put(('lab.py', ['--shots', 'holoanim', '--art', 'none', '--quality', 'ultra', '--samples', '512'], 'holo'))
if 'render' not in SKIP:
    # Shot by shot (every GPU on one shot's slices before the next): if the night runs out,
    # the shots that are done are whole.
    for s in SHOTS:
        for k in range(SLICES):
            if s in LAB:
                jobs.put(('lab.py', ['--shots', s, '--art', 'none', '--stage', 'render',
                                     '--slice', f'{k}/{SLICES}'] + OVERRIDE + NODUST_LAB, f'{s}-{k}'))
            else:
                jobs.put(('arrival.py', ['--shot', s, '--anim', '--quality', 'ultra', '--stage', 'render',
                                         '--slice', f'{k}/{SLICES}'] + OVERRIDE + NODUST_ARRIVAL, f'{s}-{k}'))
failed = []


def worker(gpu):
    while True:
        try:
            script, opts, name = jobs.get_nowait()
        except queue.Empty:
            return
        while busy(gpu):
            say(f'gpu {gpu} is in use by someone else; waiting')
            time.sleep(120)
        STARTED.add(gpu)
        say(f'gpu {gpu}: {name}')
        t = time.time()
        code = blender(script, opts, f'render-{name}.log', gpu)
        say(f'gpu {gpu}: {name} done in {(time.time() - t) / 60:.1f} min (exit {code})')
        if code:
            failed.append(name)


threads = [threading.Thread(target=worker, args=(g,)) for g in GPUS]
for t in threads:
    t.start()
for t in threads:
    t.join()
if failed:
    sys.exit(f'failed jobs: {failed}; see {LOGS}')

# 3. Film: the shots encoded for the site, and the 4K master (or the one preview file).
if 'film' not in SKIP:
    say('film')
    code = blender('film.py', ['--preview'] if args.preview else [], 'film.log', threads=32)
    say(f'film: exit {code}')
say('done')
