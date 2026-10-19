"""Real human motion for the crew: the CMU motion-capture library (mocap.cs.cmu.edu, the cgspeed BVH
release, no restrictions on use; NSF EIA-0196217), read from blender/assets/mocap/bvh/.

A Clip reads one BVH file and solves its skeleton (forward kinematics, rotations and positions per
frame). It turns into poses for crew.py's joints, in the figure's own space (facing +Y, Z up):
  pelvis       the hips' turn, tilt and roll (their heading is the shot's, so the clip's is taken out)
  spine, chest, neck, head   each one's rotation relative to the one below
  shoulder*, elbow*          aimed along the recorded upper arm and forearm
  lift         how far the hips are above their average, metres (the bob of a walk)
The legs stay crew.py's, solved to locked footprints, so nothing slides.

Walk: a single step cycle (left heel strike to the next) cut from a walk clip, so any phase of
crew.stride() has a pose: the arms and the body move in time with the feet that are really there.
Idle: a stretch of standing, played back and forth (ping-pong) so it never jumps.
"""

import math
import os

from mathutils import Euler, Matrix, Quaternion, Vector

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'mocap', 'bvh')
# BVH (Y up, facing +Z) to Blender (Z up): x, y, z → x, -z, y.
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
CI = C.transposed()
# The library's rest pose faces -Y here, the crew's faces +Y: rotations are measured from a rest
# turned half round, so a pose means the same to both.
R0 = Matrix.Rotation(math.pi, 3, 'Z')
R0I = R0.transposed()


class Joint:
    __slots__ = ('name', 'parent', 'offset', 'channels', 'children', 'index')

    def __init__(self, name, parent):
        self.name, self.parent, self.offset, self.channels, self.children = name, parent, Vector(), [], []


def _read(path):
    words = open(path).read().split()
    i = 0
    joints, stack = [], []
    cur = None
    while words[i] != 'MOTION':
        w = words[i]
        if w in ('ROOT', 'JOINT'):
            cur = Joint(words[i + 1], stack[-1] if stack else None)
            if cur.parent:
                cur.parent.children.append(cur)
            joints.append(cur)
            i += 2
        elif w == 'End':  # End Site: an offset block with nothing in it we need
            depth = 0
            i += 2
            while True:
                if words[i] == '{':
                    depth += 1
                elif words[i] == '}':
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            i += 1
        elif w == '{':
            stack.append(cur)
            i += 1
        elif w == '}':
            stack.pop()
            i += 1
        elif w == 'OFFSET':
            cur.offset = Vector([float(v) for v in words[i + 1:i + 4]])
            i += 4
        elif w == 'CHANNELS':
            n = int(words[i + 1])
            cur.channels = words[i + 2:i + 2 + n]
            i += 2 + n
        else:
            i += 1
    nframes = int(words[i + 2])
    dt = float(words[i + 5])
    vals = [float(v) for v in words[i + 6:]]
    return joints, nframes, dt, vals


class Clip:
    """One BVH: per frame, each joint's world rotation (Blender axes) and position (metres)."""

    def __init__(self, name):
        self.name = name
        joints, n, self.dt, vals = _read(os.path.join(DIR, name + '.bvh'))
        self.joints = {j.name: j for j in joints}
        width = sum(len(j.channels) for j in joints)
        # The BVH's units: scale so that the hips stand where a 1.72 m person's would (about 0.95 m).
        self.rot, self.pos = [], []
        for f in range(n):
            row = vals[f * width:(f + 1) * width]
            k = 0
            W, P = {}, {}
            for j in joints:
                loc = Vector()
                R = Matrix.Identity(3)
                for ch in j.channels:
                    v = row[k]
                    k += 1
                    if ch.endswith('position'):
                        loc['XYZ'.index(ch[0])] = v
                    else:
                        R = R @ Matrix.Rotation(math.radians(v), 3, ch[0])
                if j.parent is None:
                    W[j.name] = R
                    P[j.name] = loc + j.offset
                else:
                    W[j.name] = W[j.parent.name] @ R
                    P[j.name] = P[j.parent.name] + W[j.parent.name] @ j.offset
            self.rot.append({k2: C @ v @ CI for k2, v in W.items()})
            self.pos.append({k2: C @ v for k2, v in P.items()})
        # Units: the rest leg (hip to ankle) is set to a real person's 0.88 m.
        leg = sum((self.joints[b].offset.length for b in ('LeftLeg', 'LeftFoot')), 0.0)
        self.scale = 0.88 / leg if leg else 0.0254
        self.n = n

    def time(self, t):
        return max(0.0, min(self.n - 1.001, t / self.dt))

    def _lerp(self, table, f):
        a = int(f)
        return table[a], table[a + 1], f - a

    def heading(self, f):
        """The hips' facing (radians about Z, 0 = +Y) at frame f."""
        P = self.pos[int(f)]
        left = P['LeftUpLeg'] - P['RightUpLeg']
        left.z = 0.0
        fwd = left.cross(Vector((0, 0, 1)))
        return math.atan2(-fwd.x, fwd.y)

    def foot(self, f, side='Left'):
        return self.pos[int(f)][side + 'Foot'] * self.scale

    def pose(self, f, yaw):
        """The figure's joint rotations at (fractional) frame f, the hips' heading taken as yaw."""
        a = int(f)
        b = min(a + 1, self.n - 1)
        u = f - a
        Y = Matrix.Rotation(-yaw, 3, 'Z')

        def W(name):
            qa = (Y @ self.rot[a][name] @ R0).to_quaternion()
            qb = (Y @ self.rot[b][name] @ R0).to_quaternion()
            if qa.dot(qb) < 0:
                qb.negate()
            return qa.slerp(qb, u).to_matrix()

        def off(name):
            return R0I @ C @ self.joints[name].offset

        hips, low, sp, sp1 = W('Hips'), W('LowerBack'), W('Spine'), W('Spine1')
        neck, neck1, head = W('Neck'), W('Neck1'), W('Head')
        out = {
            'pelvis': hips.to_quaternion(),
            'spine': (hips.inverted() @ low).to_quaternion(),
            'chest': (low.inverted() @ sp1).to_quaternion(),
            'neck': (sp1.inverted() @ neck).to_quaternion(),
            'head': (neck.inverted() @ head).to_quaternion(),
        }
        down = Vector((0, 0, -1))
        for side, s in (('Left', 'L'), ('Right', 'R')):
            arm, fore = W(side + 'Arm'), W(side + 'ForeArm')
            d1 = (sp1.inverted() @ arm @ off(side + 'ForeArm')).normalized()
            d2 = (sp1.inverted() @ fore @ off(side + 'Hand')).normalized()
            q = down.rotation_difference(d1)
            out['shoulder' + s] = q
            out['elbow' + s] = down.rotation_difference(q.inverted() @ d2)
        pa, pb = self.pos[a]['Hips'], self.pos[b]['Hips']
        out['hips'] = (pa.lerp(pb, u)) * self.scale
        return out


class Walk:
    """One step cycle of a walk clip: left heel strike to the next. pose(phase) for phase in [0, 1),
    phase 0 = the left heel coming down (crew.stride()'s timing)."""

    def __init__(self, name, near=0.5):
        self.clip = c = Clip(name)
        # Left heel strikes: after a clear swing (the foot well off the ground), the first frame it
        # has slowed to a near stop. A rolling stance foot never counts: it never left the ground.
        k = max(1, int(round(0.025 / c.dt)))
        z = [c.foot(f).z for f in range(c.n)]
        floor = sorted(z)[len(z) // 20]
        down, swung = [], False
        for f in range(k, c.n - k):
            if z[f] > floor + 0.07:
                swung = True
            speed = (c.foot(f + k) - c.foot(f - k)).length / (2 * k * c.dt)
            if swung and z[f] < floor + 0.035 and speed < 0.45:
                down.append(f)
                swung = False
        # The cycle nearest `near` of the way through the clip (the steady middle of the walk).
        pairs = [(a, b) for a, b in zip(down, down[1:]) if 0.8 / c.dt < b - a < 2.0 / c.dt]
        if not pairs:
            raise ValueError(f'no step cycle in {name}')
        mid = near * c.n
        self.a, self.b = min(pairs, key=lambda p: abs((p[0] + p[1]) / 2 - mid))
        hs = [c.heading(f) for f in range(self.a, self.b)]
        self.yaw = math.atan2(sum(math.sin(h) for h in hs), sum(math.cos(h) for h in hs))
        zs = [c.pos[f]['Hips'].z * c.scale for f in range(self.a, self.b)]
        self.z = sum(zs) / len(zs)
        # The hips' sideways sway, relative to their straight-line travel through the cycle.
        p0, p1 = c.pos[self.a]['Hips'] * c.scale, c.pos[self.b]['Hips'] * c.scale
        self.p0, self.travel = p0, p1 - p0
        self.period = (self.b - self.a) * c.dt
        self.settle = _settle(c, range(self.a, self.b, 4), self.yaw, 1.0)

    def pose(self, phase):
        f = self.a + (phase % 1.0) * (self.b - self.a)
        out = _apply(self.clip.pose(f, self.yaw), self.settle)
        # Blend the last tenth of the cycle into its start so the loop never pops.
        u = (phase % 1.0)
        if u > 0.9:
            k = (u - 0.9) / 0.1
            k = k * k * (3 - 2 * k)
            start = _apply(self.clip.pose(self.a, self.yaw), self.settle)
            for key in out:
                if key == 'hips':
                    continue
                q = start[key].copy()
                if out[key].dot(q) < 0:
                    q.negate()
                out[key] = out[key].slerp(q, k)
        rel = out['hips'] - (self.p0 + self.travel * (phase % 1.0))
        rel = Matrix.Rotation(-self.yaw, 3, 'Z') @ rel
        out['lift'] = out['hips'].z - self.z
        out['sway'] = rel.x
        return out


class Idle:
    """Standing: a stretch of a standing clip, played forward and back."""

    def __init__(self, name, start=3.0, length=4.0, keep=0.35):
        self.clip = c = Clip(name)
        self.a = c.time(start)
        self.b = min(c.n - 2, self.a + length / c.dt)
        hs = [c.heading(f) for f in range(int(self.a), int(self.b))]
        self.yaw = math.atan2(sum(math.sin(h) for h in hs), sum(math.cos(h) for h in hs))
        zs = [c.pos[int(f)]['Hips'].z * c.scale for f in range(int(self.a), int(self.b))]
        self.z = sum(zs) / len(zs)
        self.settle = _settle(c, range(int(self.a), int(self.b), 6), self.yaw, keep)

    def pose(self, t):
        span = (self.b - self.a) * self.clip.dt
        u = (t / span) % 2.0
        u = u if u < 1.0 else 2.0 - u
        u = u * u * (3 - 2 * u) * 0.15 + u * 0.85  # ease the turnarounds a little
        f = self.a + u * (self.b - self.a)
        out = _apply(self.clip.pose(f, self.yaw), self.settle)
        out['lift'] = out['hips'].z - self.z
        out['sway'] = 0.0
        return out


def _mean(qs):
    """The average of rotations near each other (sign-aligned, normalised sum)."""
    ref = qs[0]
    acc = Quaternion((0, 0, 0, 0))
    for q in qs:
        q = q.copy()
        if q.dot(ref) < 0:
            q.negate()
        acc = Quaternion([a + b for a, b in zip(acc, q)])
    return acc.normalized()


def _settle(clip, frames, yaw, keep):
    """The neck's and head's average rotation over these frames: the library's conversion leaves
    a fixed tilt in them, so poses are taken relative to it (the motion stays, the tilt goes).
    keep < 1 also calms the head's movement (a recording of someone looking round a bus stop)."""
    poses = [clip.pose(f, yaw) for f in frames]
    return {k: _mean([p[k] for p in poses]).inverted() for k in ('neck', 'head')}, keep


def _apply(out, settle):
    inv, keep = settle
    for k, q in inv.items():
        r = q @ out[k]
        out[k] = Quaternion().slerp(r, keep) if keep < 1 else r
    return out


def blend(a, b, k):
    """Pose a → b by k."""
    if k <= 0:
        return a
    if k >= 1:
        return b
    out = {}
    for key, qa in a.items():
        qb = b[key]
        if isinstance(qa, Quaternion):
            qb = qb.copy()
            if qa.dot(qb) < 0:
                qb.negate()
            out[key] = qa.slerp(qb, k)
        elif isinstance(qa, Vector):
            out[key] = qa.lerp(qb, k)
        else:
            out[key] = qa + (qb - qa) * k
    return out


_cache = {}


def get(kind, name, **kw):
    key = (kind, name, tuple(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = (Walk if kind == 'walk' else Idle)(name, **kw)
    return _cache[key]


def available():
    return os.path.isdir(DIR)


__all__ = ['Clip', 'Walk', 'Idle', 'blend', 'get', 'available', 'Euler']
