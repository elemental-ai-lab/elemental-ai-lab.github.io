#!/usr/bin/env python3
"""Masthead artwork for the Elemental AI Lab website.

Particles become data. A soft ensemble of sample paths flows from a Gaussian
cloud (left), passes behind the logo and the navigation, where a radial mask
fades it almost to nothing, and converges on the nodes of three data structures
(right): a molecule (acetophenone, skeletal formula), level sets of a
two-component Gaussian mixture, and samples of a damped stochastic oscillator.
One path is steered to a marked atom and turns violet once it leaves the fade.

Every dot starts one path; every path ends on a node; every node receives
several paths, so the structures appear where the flow concentrates.

Run from the repository root:

    python3 tools/banner/generate.py           # write images/banner/*.svg
    python3 tools/banner/generate.py --check   # also print the geometry checks

Requires Python 3.9+, numpy and contourpy. The random seed is fixed, so the
output only changes when the parameters below change.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np
import contourpy

# ---------------------------------------------------------------------------
# Palette (the site's lavender line language; violet is the logo violet)
# ---------------------------------------------------------------------------
PATH = "#9c86bb"       # particle paths (drawn faint)
LINE = "#a58fc0"       # construct lines and nodes, cloud dots
VIOLET = "#7029ef"     # the steered segment and its target ring


# ---------------------------------------------------------------------------
# Small geometry helpers
# ---------------------------------------------------------------------------
def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def unit(deg):
    """Unit vector for an angle in degrees (maths convention, y up) in SVG space (y down)."""
    a = math.radians(deg)
    return np.array([math.cos(a), -math.sin(a)])


def cr_bezier(points):
    """Centripetal Catmull-Rom through points, returned as cubic Bezier segments.

    Each segment is (p1, c1, c2, p2). End tangents follow the first/last chord.
    """
    P = [np.asarray(p, float) for p in points]
    # drop consecutive duplicates
    Q = [P[0]]
    for p in P[1:]:
        if np.linalg.norm(p - Q[-1]) > 1e-6:
            Q.append(p)
    P = Q
    if len(P) < 2:
        return []
    ext = [P[0] - (P[1] - P[0])] + P + [P[-1] + (P[-1] - P[-2])]
    segs = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        d0 = max(np.linalg.norm(p1 - p0), 1e-6) ** 0.5
        d1 = max(np.linalg.norm(p2 - p1), 1e-6) ** 0.5
        d2 = max(np.linalg.norm(p3 - p2), 1e-6) ** 0.5
        t1 = (p1 - p0) / d0 - (p2 - p0) / (d0 + d1) + (p2 - p1) / d1
        t2 = (p2 - p1) / d1 - (p3 - p1) / (d1 + d2) + (p3 - p2) / d2
        c1 = p1 + t1 * d1 / 3
        c2 = p2 - t2 * d1 / 3
        segs.append((p1, c1, c2, p2))
    return segs


def bez_points(seg, n=24):
    p1, c1, c2, p2 = seg
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p1 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * p2


class Curve:
    """A path made of cubic Bezier segments (lines are degenerate cubics)."""

    def __init__(self):
        self.segs: list[tuple] = []

    def add_cr(self, points):
        self.segs.extend(cr_bezier(points))
        return self

    def add_line(self, a, b):
        a, b = np.asarray(a, float), np.asarray(b, float)
        self.segs.append((a, a + (b - a) / 3, a + 2 * (b - a) / 3, b))
        return self

    def add_arc(self, start, centre, sweep_deg):
        """Circular arc as Bezier pieces (at most 90 degrees each)."""
        start, centre = np.asarray(start, float), np.asarray(centre, float)
        r = np.linalg.norm(start - centre)
        a0 = math.atan2(start[1] - centre[1], start[0] - centre[0])
        n = max(1, int(math.ceil(abs(sweep_deg) / 90)))
        da = math.radians(sweep_deg) / n
        k = 4 / 3 * math.tan(da / 4)
        for i in range(n):
            a = a0 + i * da
            b = a + da
            p1 = centre + r * np.array([math.cos(a), math.sin(a)])
            p2 = centre + r * np.array([math.cos(b), math.sin(b)])
            c1 = p1 + k * r * np.array([-math.sin(a), math.cos(a)])
            c2 = p2 - k * r * np.array([-math.sin(b), math.cos(b)])
            self.segs.append((p1, c1, c2, p2))
        return self

    def points(self, n=24):
        pts = [bez_points(s, n) for s in self.segs]
        return np.vstack(pts) if pts else np.zeros((0, 2))

    def d(self, prec=1):
        if not self.segs:
            return ""
        f = lambda v: f"{v[0]:.{prec}f},{v[1]:.{prec}f}"
        out = [f"M{f(self.segs[0][0])}"]
        for p1, c1, c2, p2 in self.segs:
            out.append(f"C{f(c1)} {f(c2)} {f(p2)}")
        return "".join(out)

    def split_at_x(self, x_split):
        """Split into (before, after) at the first point where x >= x_split."""
        pts = self.points(48)
        idx = int(np.argmax(pts[:, 0] >= x_split))
        return pts[: idx + 1], pts[idx:]


def polyline_d(pts, prec=1):
    pts = np.asarray(pts)
    return "M" + " L".join(f"{x:.{prec}f},{y:.{prec}f}" for x, y in pts)


def segments_intersect(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def count_crossings(p, q):
    """Number of proper crossings between two polylines (vectorised-ish)."""
    n = 0
    # bounding-box prefilter per segment pair
    for i in range(len(p) - 1):
        a, b = p[i], p[i + 1]
        lo = np.minimum(a, b) - 1e-9
        hi = np.maximum(a, b) + 1e-9
        qa, qb = q[:-1], q[1:]
        qlo, qhi = np.minimum(qa, qb), np.maximum(qa, qb)
        mask = (qhi[:, 0] >= lo[0]) & (qlo[:, 0] <= hi[0]) & (qhi[:, 1] >= lo[1]) & (qlo[:, 1] <= hi[1])
        for j in np.nonzero(mask)[0]:
            if segments_intersect(a, b, qa[j], qb[j]):
                n += 1
    return n


# ---------------------------------------------------------------------------
# Constructs
# ---------------------------------------------------------------------------
# Acetophenone (9 heavy atoms), standard 2D depiction, bond length 1, maths axes.
# approach = direction (degrees) from the atom towards where its path arrives;
# always inside a gap between the atom's bonds, so no path crosses a bond.
MOLECULE_ATOMS = {
    "R0": ((1.0, 0.0), 300),
    "R1": ((0.5, 0.866), 100),
    "R2": ((-0.5, 0.866), 110),
    "R3": ((-1.0, 0.0), 240),
    "R4": ((-0.5, -0.866), 255),
    "R5": ((0.5, -0.866), 285),
    "C7": ((-2.0, 0.0), 180),
    "O": ((-2.5, 0.866), 160),
    "C8": ((-2.5, -0.866), 205),
}
MOLECULE_BONDS = [
    ("R0", "R1", 2), ("R1", "R2", 1), ("R2", "R3", 2), ("R3", "R4", 1),
    ("R4", "R5", 2), ("R5", "R0", 1), ("R3", "C7", 1), ("C7", "O", 2), ("C7", "C8", 1),
]
RING = ["R0", "R1", "R2", "R3", "R4", "R5"]
# atoms reached from above or from the left; the rest peel up from floors below the ring
UPPER_ATOMS = {"R1", "R2", "O", "C7", "C8"}


@dataclass
class Node:
    key: str
    pos: np.ndarray
    approach: np.ndarray      # unit vector from node towards incoming path
    kind: str                 # molecule | field | signal
    reach: float = 18.0       # length of the straight final approach
    extra: dict = field(default_factory=dict)


def build_molecule(centre, bond, atoms_subset=None):
    cx, cy = centre
    nodes = {}
    for key, ((x, y), ang) in MOLECULE_ATOMS.items():
        if atoms_subset and key not in atoms_subset:
            continue
        pos = np.array([cx + x * bond, cy - y * bond])
        nodes[key] = Node(key, pos, unit(ang), "molecule")
    lines = []
    ring_c = np.mean([nodes[k].pos for k in RING if k in nodes], axis=0) if all(k in nodes for k in RING) else None
    for a, b, order in MOLECULE_BONDS:
        if a not in nodes or b not in nodes:
            continue
        pa, pb = nodes[a].pos, nodes[b].pos
        lines.append((pa, pb))
        if order == 2:
            v = pb - pa
            nrm = np.array([-v[1], v[0]]) / np.linalg.norm(v)
            if a in RING and b in RING and ring_c is not None:
                # inner line of an aromatic double bond, shortened at both ends
                mid = (pa + pb) / 2
                if np.dot(ring_c - mid, nrm) < 0:
                    nrm = -nrm
                off = 0.2 * bond * nrm
                s = 0.17
                lines.append((pa + v * s + off, pb - v * s + off))
            else:
                # carbonyl: a parallel line on the outer side
                off = 0.2 * bond * nrm
                if ring_c is not None and np.dot(off, (pa + pb) / 2 - ring_c) < 0:
                    off = -off
                s = 0.12
                lines.append((pa + v * s + off, pb - v * s + off))
    return nodes, lines


def gmm_density(X, Y, comps):
    Z = np.zeros_like(X)
    for w, mu, cov in comps:
        cov = np.asarray(cov)
        inv = np.linalg.inv(cov)
        det = np.linalg.det(cov)
        dx, dy = X - mu[0], Y - mu[1]
        q = inv[0, 0] * dx * dx + 2 * inv[0, 1] * dx * dy + inv[1, 1] * dy * dy
        Z += w * np.exp(-0.5 * q) / (2 * math.pi * math.sqrt(det))
    return Z


FIELD_COMPONENTS = [
    (0.68, (-0.18, 0.04), [[0.42, 0.10], [0.10, 0.22]]),
    (0.32, (0.52, -0.10), [[0.18, -0.03], [-0.03, 0.12]]),
]


def leftmost_crossing(curve, y):
    """Left-most point where a closed polyline crosses the horizontal line at y."""
    best = None
    pts = np.vstack([curve, curve[:1]])
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            x = x0 + (y - y0) / (y1 - y0) * (x1 - x0)
            if best is None or x < best:
                best = x
    return best


def build_field(centre, scale, levels, node_specs):
    """Level sets of a two-component Gaussian mixture, scaled into the frame.

    node_specs: (level_index, dy) pairs; each node sits where the horizontal line
    centre_y + dy * scale first meets that level set from the left, and is reached
    horizontally, so the approach lines are parallel and never cross.
    """
    g = np.linspace(-2.6, 2.6, 521)
    X, Y = np.meshgrid(g, g)
    Z = gmm_density(X, Y, FIELD_COMPONENTS)
    gen = contourpy.contour_generator(X, Y, Z)
    curves = []
    for lev in levels:
        best = max(gen.lines(lev), key=len)
        pts = np.column_stack([centre[0] + best[:, 0] * scale, centre[1] - best[:, 1] * scale])
        curves.append(pts)
    nodes = {}
    for idx, (li, dy) in enumerate(node_specs):
        y = centre[1] + dy * scale
        x = leftmost_crossing(curves[li], y)
        if x is None:
            raise ValueError(f"field node {idx}: level {li} does not reach dy={dy}")
        nodes[f"F{idx}"] = Node(f"F{idx}", np.array([x, y]), np.array([-1.0, 0.0]), "field",
                                extra={"level": li, "angle": dy})
    return nodes, curves


def oscillator(n, seed, zeta=0.08, omega=2 * math.pi * 0.27, sigma=0.32, T=9.0):
    rng = np.random.default_rng(seed)
    dt = 0.002
    steps = int(T / dt)
    x, v = 0.6, 0.0
    xs = np.empty(steps)
    for i in range(steps):
        a = -2 * zeta * omega * v - omega * omega * x
        v += a * dt + sigma * math.sqrt(dt) * rng.standard_normal()
        x += v * dt
        xs[i] = x
    t = np.arange(steps) * dt
    # window that excludes the start-up transient
    t0, t1 = 1.5, T - 0.3
    sample_t = np.linspace(t0, t1, n)
    idx = np.searchsorted(t, sample_t)
    trace_mask = (t >= t0) & (t <= t1)
    return t[trace_mask], xs[trace_mask], sample_t, xs[np.clip(idx, 0, steps - 1)]


def build_signal(x0, x1, n, y_top, y_bot, seed, cycles=0.27):
    t, xs, st, sv = oscillator(n, seed, omega=2 * math.pi * cycles)
    lo, hi = xs.min(), xs.max()
    def to_y(v):
        return y_bot - (v - lo) / (hi - lo) * (y_bot - y_top)
    def to_x(tt):
        return x0 + (tt - st[0]) / (st[-1] - st[0]) * (x1 - x0)
    nodes = {}
    for i, (tt, vv) in enumerate(zip(st, sv)):
        p = np.array([to_x(tt), to_y(vv)])
        nodes[f"S{i}"] = Node(f"S{i}", p, np.array([0.0, 1.0]), "signal")
    trace = np.column_stack([to_x(t), to_y(xs)])
    keep = np.linspace(0, len(trace) - 1, 260).astype(int)
    return nodes, trace[keep]


# ---------------------------------------------------------------------------
# Compositions (frame units; the CSS places logo and navigation in the same frame)
# ---------------------------------------------------------------------------
@dataclass
class Soft:
    name: str
    W: float
    H: float
    margin: float
    seed: int
    per_node: float                  # paths per node (fractional: some nodes get one more)
    cloud: tuple                     # (cx, cy, sx, sy, xmin, xmax, ymin, ymax)
    centre_line: list                # [(x, y), ...] the stream's spine
    pull: float                      # how strongly the middle of a path follows the spine
    noise: float                     # amplitude of each path's smooth wobble
    fade: list                       # [(x, y, w, h), ...] boxes behind the logo and the navigation
    molecule: Optional[dict] = None
    fieldspec: Optional[dict] = None
    signal: Optional[dict] = None
    steer_target: str = "R4"
    violet_from: float = 0.0         # x where the steered path turns violet (outside the fade)
    reach: float = 15.0
    dot_r: float = 1.6
    node_r: float = 2.2
    path_opacity: tuple = (0.13, 0.24)
    slices: Optional[tuple] = None    # (x_first, x_last, n): snapshots of the ensemble in time
    axis_y: float = 0.0               # time axis (shares the signal's baseline when there is one)
    slice_every: int = 2              # mark every n-th path where it crosses a slice
    fade_sigma: float = 28.0          # softness of the fade boxes (blur, frame units)


def wide_soft(variant="primary"):
    S = Soft(
        name="wide", W=1440, H=420, margin=30, seed=7, per_node=1,
        cloud=(205, 222, 58, 52, 52, 395, 70, 372),
        centre_line=[(0, 214), (260, 222), (520, 252), (720, 262), (930, 250), (1120, 214), (1440, 196)],
        pull=0.72, noise=13,
        fade=[(482, 66, 476, 132), (566, 206, 308, 88)], fade_sigma=24,
        molecule=dict(centre=(1316, 134), bond=27),
        fieldspec=dict(centre=(1162, 262), scale=42, levels=(0.075, 0.18, 0.30),
                       node_specs=[(0, -0.74), (1, -0.56), (0, -0.38), (2, -0.20), (1, -0.02),
                                   (2, 0.16), (0, 0.34), (1, 0.50), (0, 0.66)]),
        signal=dict(x0=1246, x1=1388, n=10, y_top=300, y_bot=356, seed=11, cycles=0.27),
        violet_from=1075, slices=(445, 1062, 7), axis_y=370, slice_every=1,
        path_opacity=(0.16, 0.28),
    )
    if variant == "sparse":
        S = replace(S, seed=5, per_node=1, noise=10, path_opacity=(0.2, 0.32),
                    fieldspec=dict(centre=(1160, 264), scale=50, levels=(0.075, 0.20),
                                   node_specs=[(0, -0.6), (1, -0.3), (0, 0.0), (1, 0.3), (0, 0.6)]),
                    signal=dict(x0=1262, x1=1384, n=6, y_top=296, y_bot=354, seed=11, cycles=0.16))
    return S


def medium_soft(variant="primary"):
    """Tablets (640-1023 px): drawn at the masthead's height and cropped at the sides; the
    cloud and the end of the signal may run off the edges, everything else stays in view."""
    S = Soft(
        name="medium", W=1030, H=300, margin=12, seed=21, per_node=1,
        cloud=(205, 160, 70, 40, 30, 340, 70, 255),
        centre_line=[(0, 158), (300, 168), (515, 186), (720, 178), (1030, 160)],
        pull=0.7, noise=9,
        fade=[(339, 46, 352, 96), (404, 140, 222, 78)], fade_sigma=18,
        molecule=dict(centre=(812, 98), bond=18),
        fieldspec=dict(centre=(782, 186), scale=26, levels=(0.075, 0.20),
                       node_specs=[(0, -0.62), (1, -0.36), (0, -0.10), (1, 0.16), (0, 0.42)]),
        signal=dict(x0=836, x1=1012, n=11, y_top=222, y_bot=252, seed=11, cycles=0.25),
        violet_from=700, reach=12.0, dot_r=1.4, node_r=2.0, slices=(360, 730, 5), axis_y=266, slice_every=1,
        path_opacity=(0.16, 0.28),
    )
    if variant == "sparse":
        S = replace(S, seed=23, per_node=1, path_opacity=(0.2, 0.32),
                    fieldspec=dict(centre=(782, 186), scale=28, levels=(0.075, 0.20),
                                   node_specs=[(0, -0.5), (1, 0.0), (0, 0.5)]),
                    signal=dict(x0=836, x1=1012, n=7, y_top=222, y_bot=252, seed=11, cycles=0.18))
    return S


def narrow_soft(variant="primary"):
    """Phones (below 640 px): same masthead height as tablets, cropped at the sides."""
    S = Soft(
        name="narrow", W=640, H=272, margin=14, seed=31, per_node=1,
        cloud=(118, 210, 50, 22, 22, 240, 160, 255),
        centre_line=[(0, 210), (200, 216), (322, 226), (420, 236), (640, 222)],
        pull=0.6, noise=6,
        fade=[(190, 42, 260, 74), (218, 132, 204, 60)], fade_sigma=12,
        molecule=dict(centre=(322, 226), bond=11),
        fieldspec=None,
        signal=dict(x0=382, x1=470, n=8, y_top=214, y_bot=238, seed=11, cycles=0.2),
        violet_from=252, reach=7.5, dot_r=1.2, node_r=1.7, slices=(175, 268, 4), axis_y=252, slice_every=1,
        path_opacity=(0.18, 0.3),
    )
    if variant == "sparse":
        S = replace(S, seed=33, per_node=1, path_opacity=(0.2, 0.32),
                    signal=dict(x0=382, x1=470, n=5, y_top=214, y_bot=238, seed=11, cycles=0.14))
    return S


def spine(S: Soft):
    pts = np.array(S.centre_line, float)
    dense = Curve().add_cr(pts).points(40)
    order = np.argsort(dense[:, 0])
    xs, ys = dense[order, 0], dense[order, 1]
    return lambda x: np.interp(x, xs, ys)


def flow_path(S: Soft, start, node: Node, rng, c, noise=True, pull=None):
    """Smooth path: start -> (spine-following body) -> pre-approach -> approach -> node."""
    r = S.reach
    if node.kind == "signal":
        # arrive along the bottom, then rise up the stem into the sample
        base = S.signal["y_bot"] + 14
        far = np.array([node.pos[0] - 2.6 * r, base + 0.7 * r])
        q = np.array([node.pos[0] - 0.2 * r, base + 0.25 * r])
        a = np.array([node.pos[0], base - 0.7 * r])
    else:
        far = node.pos + node.approach * r * 3.0
        q = node.pos + node.approach * r * 1.9
        a = node.pos + node.approach * r
    x0, y0 = start
    n_body = max(6, int(abs(far[0] - x0) / 26))
    t = np.linspace(0, 1, n_body)
    xs = x0 + (far[0] - x0) * t
    s = smoothstep(t)
    base_y = (1 - s) * y0 + s * far[1]
    p = (S.pull if pull is None else pull) * np.sin(np.pi * t) ** 2
    ys = base_y + p * (c(xs) - base_y)
    if noise:
        amp = S.noise * rng.uniform(0.5, 1.0)
        wob = sum(rng.uniform(-1, 1) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi)) for f in (0.7, 1.3, 2.1))
        ys = ys + amp * wob / 2.2 * np.sin(np.pi * t) ** 1.5
    pts = list(zip(xs, ys)) + [tuple(q), tuple(a), tuple(node.pos)]
    return Curve().add_cr(pts)


def compose_soft(S: Soft):
    rng = np.random.default_rng(S.seed)
    nodes, mol_lines, field_curves, signal_trace = {}, [], [], None
    if S.molecule:
        mn, mol_lines = build_molecule(S.molecule["centre"], S.molecule["bond"])
        nodes.update(mn)
    if S.fieldspec:
        f = S.fieldspec
        fn, field_curves = build_field(f["centre"], f["scale"], f["levels"], f["node_specs"])
        nodes.update(fn)
    if S.signal:
        s = S.signal
        sn, signal_trace = build_signal(s["x0"], s["x1"], s["n"], s["y_top"], s["y_bot"], s["seed"], s.get("cycles", 0.27))
        nodes.update(sn)
    c = spine(S)

    steer_key = S.steer_target if S.steer_target in nodes else None
    base_n = int(S.per_node); frac = S.per_node - base_n
    targets = [k for k in nodes if k != steer_key for _ in range(base_n + (1 if rng.random() < frac else 0))]
    n = len(targets)
    cx, cy, sx, sy, xmin, xmax, ymin, ymax = S.cloud
    starts = []
    while len(starts) < n + 1:
        x, y = rng.normal(cx, sx), rng.normal(cy, sy)
        if xmin <= x <= xmax and ymin <= y <= ymax:
            starts.append((x, y))
    starts = np.array(starts)
    steer_start = starts[-1]
    starts = starts[:-1]
    # rank matching with a little shuffle keeps the stream orderly but not combed
    far_y = {k: (nodes[k].pos[1] + 30 if nodes[k].kind == 'signal' else (nodes[k].pos + nodes[k].approach * S.reach * 3.0)[1]) for k in nodes}
    tgt_order = sorted(targets, key=lambda k: far_y[k] + rng.normal(0, 14))
    src_order = np.argsort(starts[:, 1] + rng.normal(0, 18, n))
    paths = []
    for k, i in zip(tgt_order, src_order):
        cv = flow_path(S, starts[i], nodes[k], rng, c)
        paths.append(dict(curve=cv, start=starts[i], node=nodes[k],
                          opacity=float(np.round(rng.uniform(*S.path_opacity), 3))))
    steer = None
    if S.steer_target in nodes:
        steer = dict(curve=flow_path(S, steer_start, nodes[S.steer_target], rng, c, noise=False, pull=0.8),
                     start=steer_start, node=nodes[S.steer_target])
    return dict(S=S, nodes=nodes, paths=paths, steer=steer, mol_lines=mol_lines,
                field_curves=field_curves, signal_trace=signal_trace)


def soft_svg(C, title, desc):
    S = C["S"]
    W, H = S.W, S.H
    sw = 'vector-effect="non-scaling-stroke"'
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" preserveAspectRatio="xMidYMid meet">',
         f"<title>{title}</title>", f"<desc>{desc}</desc>",
         "<defs>",
         # soft-edged fade behind the logo and the navigation (luminance mask)
         f'<filter id="fadeBlur" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="{S.fade_sigma:g}"/></filter>',
         f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W:g}" height="{H:g}">'
         f'<rect width="{W:g}" height="{H:g}" fill="#fff"/><g filter="url(#fadeBlur)">'
         + "".join(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{min(w, h) / 2:g}" fill="#000" fill-opacity=".88"/>' for x, y, w, h in S.fade)
         + '</g></mask>',
         # the stream gathers gradually out of the cloud
         f'<linearGradient id="inG" gradientUnits="userSpaceOnUse" x1="{S.cloud[4]:g}" y1="0" x2="{S.cloud[1] * 0 + S.cloud[5] + 60:g}" y2="0">'
         f'<stop offset="0" stop-color="{PATH}" stop-opacity=".35"/><stop offset="1" stop-color="{PATH}"/></linearGradient>',
         f'<linearGradient id="violetG" gradientUnits="userSpaceOnUse" x1="{S.violet_from:g}" y1="0" x2="{S.violet_from + 0.07 * W:g}" y2="0">'
         f'<stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/><stop offset="1" stop-color="{VIOLET}"/></linearGradient>',
         "</defs>",
         f'<g mask="url(#fade)" fill="none" stroke="url(#inG)" stroke-width=".9" stroke-linecap="round" {sw}>']
    for p in C["paths"]:
        o.append(f'<path d="{p["curve"].d()}" stroke-opacity="{p["opacity"]}" {sw}/>')
    st = C["steer"]
    if st:
        before, after = st["curve"].split_at_x(S.violet_from)
        lav, _ = st["curve"].split_at_x(S.violet_from + 0.07 * S.W)
        o.append(f'<path d="{polyline_d(lav)}" stroke-opacity=".55" {sw}/>')
    o.append("</g>")
    if S.slices:
        rs = np.random.default_rng(S.seed + 7)
        xs_s = np.linspace(*S.slices)
        o.append(f'<g mask="url(#fade)" fill="none" stroke="{PATH}" stroke-width=".8" stroke-dasharray="1.5 4" stroke-opacity=".32" {sw}>')
        for xk in xs_s:
            o.append(f'<path d="M{xk:.1f},{S.axis_y - 5:.1f}V{S.margin + 4:.1f}" {sw}/>')
        o.append("</g>")
        o.append(f'<g mask="url(#fade)" fill="{PATH}" fill-opacity=".62">')
        for idx, p in enumerate(C["paths"]):
            if idx % S.slice_every:
                continue
            pts = p["curve"].points(12)
            for xk in xs_s:
                j = int(np.argmax(pts[:, 0] >= xk))
                if j == 0 or pts[-1, 0] < xk:
                    continue
                (x1, y1), (x2, y2) = pts[j - 1], pts[j]
                y = y1 + (xk - x1) / max(x2 - x1, 1e-6) * (y2 - y1)
                o.append(f'<circle cx="{xk:.1f}" cy="{y:.1f}" r="{rs.uniform(0.6, 1.5):.2f}"/>')
        o.append("</g>")
        # time runs left to right; with a signal, the axis runs into the signal's baseline
        step = xs_s[1] - xs_s[0] if len(xs_s) > 1 else 40
        x0a = xs_s[0] - 0.35 * step
        x1a = (S.signal["x0"] - 10) if S.signal else xs_s[-1] + 0.6 * step
        ay = S.axis_y
        o.append(f'<g fill="none" stroke="{LINE}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" {sw}>')
        o.append(f'<path d="M{x0a:.1f},{ay:.1f}H{x1a:.1f}" stroke-opacity=".7" {sw}/>')
        for xk in xs_s:
            o.append(f'<path d="M{xk:.1f},{ay - 4:.1f}V{ay + 4:.1f}" stroke-opacity=".7" {sw}/>')
        o.append(f'<path d="M{x1a - 7:.1f},{ay - 4:.1f}L{x1a:.1f},{ay:.1f}L{x1a - 7:.1f},{ay + 4:.1f}" stroke-opacity=".8" {sw}/>')
        o.append("</g>")
    o.append(f'<g mask="url(#fade)" fill="{LINE}">')
    for p in C["paths"]:
        o.append(f'<circle cx="{p["start"][0]:.1f}" cy="{p["start"][1]:.1f}" r="{S.dot_r:g}" fill-opacity=".55"/>')
    if st:
        o.append(f'<circle cx="{st["start"][0]:.1f}" cy="{st["start"][1]:.1f}" r="{S.dot_r:g}"/>')
    o.append("</g>")
    # data structures: crisp, outside the fade
    o.append(f'<g fill="none" stroke="{LINE}" stroke-width="1" stroke-linecap="round" {sw}>')
    for a, b in C["mol_lines"]:
        o.append(f'<path d="M{a[0]:.1f},{a[1]:.1f}L{b[0]:.1f},{b[1]:.1f}" {sw}/>')
    for cv in C["field_curves"]:
        cc = Curve(); cc.segs = cr_bezier(np.vstack([cv[::6], cv[:1]]))
        o.append(f'<path d="{cc.d()}Z" {sw}/>')
    if C["signal_trace"] is not None:
        sig = sorted([nd for nd in C["nodes"].values() if nd.kind == "signal"], key=lambda nd: nd.pos[0])
        base = S.signal["y_bot"] + 14
        o.append(f'<path d="M{sig[0].pos[0]:.1f},{base:.1f}H{sig[-1].pos[0]:.1f}" stroke-opacity=".55" {sw}/>')
        for nd in sig:
            o.append(f'<path d="M{nd.pos[0]:.1f},{base:.1f}V{nd.pos[1]:.1f}" {sw}/>')
        o.append(f'<path d="{polyline_d(C["signal_trace"])}" {sw}/>')
    o.append("</g>")
    if st:
        o.append(f'<path d="{polyline_d(after)}" fill="none" stroke="url(#violetG)" stroke-width="1.15" stroke-linecap="round" {sw}/>')
    o.append(f'<g fill="{LINE}">')
    for nd in C["nodes"].values():
        if st and nd.key == st["node"].key:
            continue
        o.append(f'<circle cx="{nd.pos[0]:.1f}" cy="{nd.pos[1]:.1f}" r="{S.node_r:g}"/>')
    o.append("</g>")
    if st:
        p = st["node"].pos
        o.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{S.node_r:g}" fill="{VIOLET}"/>')
        o.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{S.node_r * 3:g}" fill="none" stroke="{VIOLET}" stroke-width="1" {sw}/>')
    o.append("</svg>")
    return "\n".join(o)


def compact_svg(W=1440, H=200, n=22, seed=41, title="", desc=""):
    """Sub-page header: the stream as a ribbon, fading behind the logo and the navigation,
    with one violet path leaving it. Drawn at the header's height and cropped at the sides."""
    rng = np.random.default_rng(seed)
    sw = 'vector-effect="non-scaling-stroke"'
    boxes = [(592, 16, 256, 74), (590, 106, 260, 68)]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet">',
         f"<title>{title}</title>", f"<desc>{desc}</desc>", "<defs>",
         '<filter id="fadeBlur" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="13"/></filter>',
         f'<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="#fff"/>'
         '<g filter="url(#fadeBlur)">' + "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{min(w, h) / 2:g}" fill="#000" fill-opacity=".88"/>' for x, y, w, h in boxes)
         + '</g></mask>',
         f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0"><stop offset="0" stop-color="{PATH}" stop-opacity="0"/>'
         f'<stop offset=".14" stop-color="{PATH}"/><stop offset=".86" stop-color="{PATH}"/><stop offset="1" stop-color="{PATH}" stop-opacity="0"/></linearGradient>',
         f'<linearGradient id="v" gradientUnits="userSpaceOnUse" x1="858" y1="0" x2="922" y2="0"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0"/>'
         f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>',
         "</defs>", f'<g mask="url(#fade)" fill="none" stroke="url(#g)" stroke-width=".9">']
    for i in range(n):
        pts = []
        ph1, ph2 = rng.uniform(0, 2 * np.pi, 2)
        amp = rng.uniform(1.0, 2.6)
        for x in np.linspace(-20, W + 20, 30):
            t = x / W
            spread = 1.0 - 0.45 * math.sin(math.pi * t)
            y = (142 + 5 * math.sin(2 * math.pi * t * 0.9 + 0.4) + (i - (n - 1) / 2) * 1.7 * spread
                 + amp * math.sin(3 * math.pi * t + ph1) + 0.8 * math.sin(7 * math.pi * t + ph2))
            pts.append((x, y))
        o.append(f'<path d="{Curve().add_cr(pts).d()}" stroke-opacity="{rng.uniform(.16, .28):.2f}" {sw}/>')
    o.append("</g>")
    # the steered path runs inside the ribbon, then leaves it and rises to a point
    sp = [(x, 142 + 5 * math.sin(2 * math.pi * (x / W) * 0.9 + 0.4)) for x in np.linspace(-20, 880, 25)]
    sp += [(914, 136), (940, 118), (960, 96), (972, 80)]
    cv = Curve().add_cr(sp)
    before, after = cv.split_at_x(858)
    o.append(f'<path mask="url(#fade)" d="{polyline_d(before)}" fill="none" stroke="url(#g)" stroke-opacity=".5" stroke-width=".9" {sw}/>')
    o.append(f'<path d="{polyline_d(after)}" fill="none" stroke="url(#v)" stroke-width="1.15" stroke-linecap="round" {sw}/>')
    o.append(f'<circle cx="972" cy="80" r="2.3" fill="{VIOLET}"/>')
    o.append("</svg>")
    return "\n".join(o)


def checks_soft(C):
    S = C["S"]
    polys = [p["curve"].points(16) for p in C["paths"]]
    if C["steer"]:
        polys.append(C["steer"]["curve"].points(16))
    allp = np.vstack(polys)
    m = S.margin
    out = ((allp[:, 0] < m) | (allp[:, 0] > S.W - m) | (allp[:, 1] < m) | (allp[:, 1] > S.H - m)).sum()
    received = {k: 0 for k in C["nodes"]}
    for p in C["paths"]:
        received[p["node"].key] += 1
    if C["steer"]:
        received[C["steer"]["node"].key] += 1
    return {"layout": S.name, "paths": len(C["paths"]) + (1 if C["steer"] else 0), "dots": len(C["paths"]) + (1 if C["steer"] else 0),
            "nodes": len(C["nodes"]), "min_paths_per_node": min(received.values()), "max_paths_per_node": max(received.values()),
            "points_outside_margin": int(out)}


LAYOUTS = {"wide": wide_soft, "medium": medium_soft, "narrow": narrow_soft}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="images/banner")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    title = "Particles become data"
    desc = ("A soft stream of particle paths flows from a cloud on the left along a time axis, fades behind "
            "the lab name and navigation, and gathers into a molecule, a contour map and a sampled signal. Dotted "
            "slices mark the particles at successive moments. One violet path is steered to a marked atom.")
    for name, fn in LAYOUTS.items():
        for variant in ("primary", "sparse"):
            C = compose_soft(fn(variant))
            suffix = "" if variant == "primary" else "-sparse"
            with open(os.path.join(args.out, f"masthead-{name}{suffix}.svg"), "w") as f:
                f.write(soft_svg(C, title, desc))
            if args.check:
                print(json.dumps(checks_soft(C)))
    with open(os.path.join(args.out, "masthead-compact.svg"), "w") as f:
        f.write(compact_svg(title="Particle paths", desc="A ribbon of particle paths with one violet path leaving it."))


if __name__ == "__main__":
    main()
