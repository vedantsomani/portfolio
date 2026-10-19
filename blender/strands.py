"""Real hair for the briefing's two people: strand by strand curves (Blender's hair curves), shaded
with the physically based hair BSDF (melanin, not paint), each hair tapering to its tip.

  vedant     dark, thick and a little wavy: long on top (swept up and back, with volume), short at
             the sides and the back; and a short beard of stubble along the jaw, chin and upper lip
  ponytail   pulled back over the scalp to a tie at the back of the head, a tail hanging from it

Built in the body's rest pose (it faces -Y here) and hung from the head bone, so it moves with the
head. human.py calls grow(body, rig, style)."""

import math
import random

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def _scalp(body, rig):
    """The skull's centre and the body's surface as (point, normal, triangle area) samples."""
    head_b = rig.data.bones['mixamorig:Head']
    hb = rig.matrix_world @ head_b.head_local
    ht = rig.matrix_world @ head_b.tail_local
    hc = hb.lerp(ht, 0.45)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    mw = body.matrix_world
    nm = mw.to_3x3()
    tris = []
    for t in me.loop_triangles:
        a, b, c = (mw @ me.vertices[i].co for i in t.vertices)
        cen = (a + b + c) / 3
        if (cen - hc).length > 0.17:
            continue
        n = (nm @ t.normal).normalized()
        tris.append((a, b, c, n, t.area))
    ev.to_mesh_clear()
    return hc, hb, tris


def _sample(tris, keep, count, rng):
    """count points spread over the triangles keep() accepts, by area: (point, normal, keep's value)."""
    chosen = []
    for a, b, c, n, area in tris:
        cen = (a + b + c) / 3
        w = keep(cen)
        if w > 0:
            chosen.append((a, b, c, n, area * w, w))
    total = sum(x[4] for x in chosen)
    out = []
    for a, b, c, n, wa, w in chosen:
        k = wa / total * count
        m = int(k) + (1 if rng.random() < k - int(k) else 0)
        for _ in range(m):
            u, v = rng.random(), rng.random()
            if u + v > 1:
                u, v = 1 - u, 1 - v
            out.append((a + (b - a) * u + (c - a) * v, n, w))
    return out


def _angles(p, hc):
    r = p - hc
    az = math.degrees(math.atan2(r.x, -r.y))  # 0 = the front (the face looks along -Y)
    el = math.degrees(math.atan2(r.z, math.hypot(r.x, r.y)))
    return az, el


def _smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _hairline(az):
    """The lowest elevation (degrees, round the skull's centre) hair grows at, by azimuth: high on
    the forehead, above the ears at the sides, down to the nape at the back."""
    c = math.cos(math.radians(az))
    return -2 + 34 * c if c >= 0 else -2 + 40 * c


def _material(name, melanin, redness, rough=0.32):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    h = nt.nodes.new('ShaderNodeBsdfHairPrincipled')
    try:
        h.model = 'HUANG'
    except TypeError:
        pass
    h.parametrization = 'MELANIN'
    h.inputs['Melanin'].default_value = melanin
    h.inputs['Melanin Redness'].default_value = redness
    h.inputs['Roughness'].default_value = rough
    if 'Radial Roughness' in h.inputs:
        h.inputs['Radial Roughness'].default_value = 0.4
    if 'Random Roughness' in h.inputs:
        h.inputs['Random Roughness'].default_value = 0.2
    if 'Random Color' in h.inputs:
        h.inputs['Random Color'].default_value = 0.08
    nt.links.new(h.outputs[0], out.inputs['Surface'])
    return m


def _curves(name, strands, root_r, tip_r, mat, rig):
    """A hair curves object from strands (lists of points), hung from the head bone."""
    hc = bpy.data.hair_curves.new(name)
    hc.add_curves([len(s) for s in strands])
    flat, radius = [], []
    for s in strands:
        n = len(s)
        for i, p in enumerate(s):
            flat += [p.x, p.y, p.z]
            u = i / (n - 1)
            radius.append(root_r + (tip_r - root_r) * u ** 0.7)
    hc.position_data.foreach_set('vector', flat)
    rad = hc.attributes.get('radius') or hc.attributes.new('radius', 'FLOAT', 'POINT')
    rad.data.foreach_set('value', radius)
    hc.materials.append(mat)
    ob = bpy.data.objects.new(name, hc)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig
    ob.parent_type = 'BONE'
    ob.parent_bone = 'mixamorig:Head'
    bpy.context.view_layer.update()
    ob.matrix_world = mw
    return ob


def _grow(roots, hc, path, points, clumps, clump, frizz, rng, guard=0.003):
    """Strands from roots: path(root, normal, w, u) gives each one's point at u (0 root → 1 tip);
    strands gather towards their clump's leader by clump * u (so tips group as real hair does),
    a little frizz on top, and no point is let inside the skull."""
    paths = [[path(p, n, w, i / (points - 1)) for i in range(points)] for p, n, w in roots]
    lead = rng.sample(range(len(roots)), min(clumps, len(roots)))
    kd = KDTree(len(lead))
    for k, i in enumerate(lead):
        kd.insert(roots[i][0], k)
    kd.balance()
    out = []
    for (p, n, w), s in zip(roots, paths):
        _, k, _ = kd.find(p)
        g = paths[lead[k]]
        r0 = (p - hc).length
        strand = []
        for i, q in enumerate(s):
            u = i / (points - 1)
            q = q + ((g[i] - g[0]) - (q - s[0])) * clump * u ** 1.3
            q = q + Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))) * frizz * u
            d = q - hc
            if d.length < r0 + guard * min(1.0, u * 4):
                q = hc + d.normalized() * (r0 + guard * min(1.0, u * 4))
            strand.append(q)
        out.append(strand)
    return out


def _vedant(body, rig, rng):
    hc, hb, tris = _scalp(body, rig)
    back, up = Vector((0, 1, 0)), Vector((0, 0, 1))

    def on_scalp(p):
        az, el = _angles(p, hc)
        return 1.0 if el > _hairline(az) and (p - hc).length < 0.14 else 0.0

    roots = _sample(tris, on_scalp, 70000, rng)

    def length(p):
        az, el = _angles(p, hc)
        top = _smooth((el - 30) / 30)  # the crown and the top: long
        front = _smooth((math.cos(math.radians(az)) - 0.3) / 0.6)
        side = 1 - top
        return 0.024 * side + top * (0.058 + 0.016 * front)

    def heading(p, n, s_):
        """Which way the strand runs at s_ along it: on top, up off the scalp with body and then
        swept back; at the sides, lying back and down; a slow wave through it."""
        az, el = _angles(p, hc)
        top = _smooth((el - 30) / 30)
        lift = n * (1 - s_) ** 1.3 * 0.75 + up * 0.3 * (1 - s_)
        d_top = lift + back * (0.3 + 0.9 * s_) - up * 0.25 * s_ * s_
        down_back = back * 0.7 - up * 0.6
        t = (down_back - n * down_back.dot(n)).normalized()
        d_side = t + n * 0.3
        wave = Vector((math.sin(s_ * 8.0 + p.x * 140), math.sin(s_ * 5.0 + p.z * 120) * 0.5,
                       math.cos(s_ * 7.0 + p.y * 110))) * 0.22 * s_
        return (d_top * top + d_side * (1 - top) + wave).normalized()

    def path(p, n, w, u):
        L = length(p)
        q = p.copy()
        steps = 8
        for i in range(int(round(u * steps))):
            q += heading(p, n, i / steps) * (L / steps)
        return q

    strands = _grow(roots, hc, path, 9, 1400, 0.42, 0.0026, rng)
    hair = _curves(f'{body.name.split("-")[0]}-hair', strands, 0.000055, 0.000018,
                   _material('vedant-hair', 0.985, 0.12, 0.34), rig)
    return hair, hc


def _beard(body, rig, rng):
    """Stubble: short dark hairs lying down along the face, densest at the chin and jaw."""
    hc, hb, tris = _scalp(body, rig)
    face = [(a + b + c) / 3 for a, b, c, n, _ in tris]
    pts = [p for p in face if p.y < hc.y - 0.02 and abs(p.x) < 0.09 and p.z > hb.z - 0.06]
    nose = min(pts, key=lambda p: p.y)
    chin = min((p for p in pts if abs(p.x) < 0.02 and p.y < hc.y - 0.06), key=lambda p: p.z)
    mouth_z = nose.z - 0.032

    def zone(p):
        """How much beard grows here (0 to 1): the jaw, chin, the cheeks' lower half and the
        upper lip, thinning out at the edge; nothing on the lips."""
        x = abs(p.x)
        top = nose.z - 0.016 + 0.35 * x  # the cheek line, rising towards the ears
        if p.y > hc.y or p.z > top or p.z < chin.z - 0.022 or x > 0.078:
            return 0.0
        if x < 0.024 and abs(p.z - mouth_z) < 0.008:
            return 0.0
        edge = min(top - p.z, 0.078 - x, p.z - (chin.z - 0.022))
        return max(0.05, min(1.0, edge / 0.014))

    roots = _sample(tris, zone, 46000, rng)
    down = Vector((0, 0, -1))

    def path(p, n, w, u):
        t = (down - n * down.dot(n)).normalized()
        L = 0.0065 * (0.55 + 0.45 * w)
        return p + (t * 0.85 + n * 0.45).normalized() * L * u

    strands = _grow(roots, hc, path, 4, 3000, 0.0, 0.0002, rng, guard=0.0)
    return _curves(f'{body.name.split("-")[0]}-beard', strands, 0.00004, 0.000015,
                   _material('beard', 0.99, 0.1, 0.4), rig)


def _ponytail(body, rig, rng):
    hc, hb, tris = _scalp(body, rig)

    def on_scalp(p):
        az, el = _angles(p, hc)
        return 1.0 if el > _hairline(az) + 4 and (p - hc).length < 0.14 else 0.0

    roots = _sample(tris, on_scalp, 45000, rng)
    tie = hc + Vector((0.0, 0.115, -0.035))  # the back of the head, a little below the crown
    tail_dir = Vector((0.0, 0.25, -1.0)).normalized()

    def path(p, n, w, u):
        # Over the scalp to the tie (u up to 0.55), then down the tail.
        if u <= 0.55:
            k = u / 0.55
            q = p.lerp(tie, _smooth(k))
            d = q - hc
            r = max((p - hc).length, (tie - hc).length) + 0.004
            return hc + d.normalized() * max(d.length, r * (1 - 0.15 * k * (1 - k)))
        k = (u - 0.55) / 0.45
        spread = Vector((rng.gauss(0, 1), rng.gauss(0, 1), 0)) * 0.012 * k
        return tie + tail_dir * 0.26 * k + spread

    strands = _grow(roots, hc, path, 12, 400, 0.35, 0.0008, rng, guard=0.002)
    return _curves(f'{body.name.split("-")[0]}-hair', strands, 0.00005, 0.000016,
                   _material('recruiter-hair', 0.9, 0.35, 0.28), rig)


def grow(body, rig, style, beard=False, seed=7):
    rng = random.Random(seed)
    made = []
    if style == 'vedant':
        made.append(_vedant(body, rig, rng)[0])
    elif style == 'ponytail':
        made.append(_ponytail(body, rig, rng))
    if beard:
        made.append(_beard(body, rig, rng))
    print('[strands]', style, ', '.join(f'{o.name} {len(o.data.curves)} hairs' for o in made), flush=True)
    return made
