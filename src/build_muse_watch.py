#!/usr/bin/env python3
"""
Muse Watch — Pixel Watch 4 (45mm) pendant + dock-while-wearing system.

Parts
  1. pendant_shell_v4.stl  : v3 scan-based shell with the charging side (left, -X)
                             cut open on a chord (x = -19.5) so the watch's left
                             edge protrudes 3.1 mm and can drop into the official
                             Quick Charge Dock puck groove.
  2. dock.stl              : PalmPilot-style cradle. Drop the pendant in rotated
                             90 deg CCW (charging edge down, crown up, necklace
                             tower + cord to the left, out the open cord bay).
                             The official puck (41 x 27 x 9.6 mm) sits in the
                             saddle pocket; gravity + the puck magnet mate the pins.
  3. puck_fit_test.stl     : small test block for the puck pocket only.
  4. pendant_dummy_docked.stl : simplified pendant silhouette in docked pose
                             (fit/visual check in a slicer, do not wear).

Pendant frame (v3, Blender/STL): X = right (crown), Y = +back / -front, Z = up.
Watch (scan-measured 2026-11-14): case r 22.6, crown dia 7.0, sensor r 14.5.
Official puck (Google tech specs): 41.0 (L) x 27.0 (W) x 9.6 (H) mm, cable 1 m.

Dock frame: X = left(-) / right(+), Y = front(-) / back(+), Z = up.
Docked transform of pendant point (x, y, z) -> ( -z, y, x ) + (10, 0, 48).
"""
import os
import numpy as np
import trimesh
from trimesh.boolean import union, difference

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
V3_SHELL = os.path.join(ROOT, "vendor_v3", "v3_part1_PLA_shell.stl")
SEG = 96


def box(size, center):
    m = trimesh.creation.box(extents=size)
    m.apply_translation(center)
    return m


def cyl(d, h, center=(0, 0, 0), axis="z", seg=SEG):
    m = trimesh.creation.cylinder(radius=d / 2, height=h, sections=seg)
    if axis == "x":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    if axis == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation(center)
    return m


def rounded_plate(sx, sy, sz, r=6.0, z0=0.0):
    """Box with vertical corners rounded (union of box + 4 corner cylinders)."""
    cx, cy = sx / 2 - r, sy / 2 - r
    parts = [box((sx - 2 * r, sy, sz), (0, 0, z0 + sz / 2)),
             box((sx, sy - 2 * r, sz), (0, 0, z0 + sz / 2))]
    for dx in (-cx, cx):
        for dy in (-cy, cy):
            parts.append(cyl(2 * r, sz, (dx, dy, z0 + sz / 2), seg=48))
    return union(parts, engine="manifold")


def export(mesh, name):
    path = os.path.join(MODELS, name)
    # ASCII STL: text, so it can live in git directly
    trimesh.exchange.export.export_mesh(mesh, path, file_type="stl_ascii")
    print(name, "watertight=", mesh.is_watertight,
          "vol_cm3=", round(float(mesh.volume) / 1000, 2),
          "bounds=", np.round(mesh.bounds, 1).tolist())


# ---------------------------------------------------------------- pendant v4
def build_pendant_shell_v4():
    shell = trimesh.load(V3_SHELL)
    # Open the charging side: cut everything with x < -19.5 (full Y/Z slab).
    # Watch edge (r22.6) then protrudes 3.1 mm beyond the cut face.
    cutter = box((24, 30, 90), (-31.5, 0, 7))
    shell = difference([shell, cutter], engine="manifold")
    # Two shallow docking guide flats on the cut face edges are implicit (flat face).
    # Small chamfer on the cut face top/bottom edges: cut 45 deg at z extremes of the face
    for zc in (-27.5, 27.5):
        ch = box((6, 30, 8), (-20.5, 0, zc))
        ch.apply_transform(trimesh.transformations.rotation_matrix(
            np.pi / 4, [0, 1, 0], point=(-19.5, 0, zc - 6 if zc < 0 else zc + 6)))
        # keep it simple: skip chamfer if it risks non-manifold; face is fine flat
    return shell


# ---------------------------------------------------------------- puck test
PUCK_L, PUCK_W, PUCK_H = 41.0, 27.0, 9.6   # official dimensions
POCKET_L, POCKET_W = PUCK_L + 1.6, PUCK_W + 1.4  # clearance for a slip fit
POCKET_FLOOR_Z = 18.9                       # in dock frame; puck top = 28.5


def build_puck_fit_test():
    block = rounded_plate(56, 40, 12, r=5, z0=0)
    pocket = box((POCKET_L, POCKET_W, 10), (0, 0, 12 - 2.6 + 5))
    cable = box((20, 7, 7), (28, 0, 8))
    return difference([block, pocket, cable], engine="manifold")


# ---------------------------------------------------------------- dock
def build_dock():
    # Base plate 124 x 92 x 8
    base = rounded_plate(124, 92, 8, r=8, z0=0)
    base.apply_translation((0, 0, 0))  # centered at origin, top z=8

    # Back wall (right portion only; left side is the open cord bay)
    # spans X -16..56, Y 11..19, Z 8..76
    wall = box((72, 8, 68), (20, 13.3, 42))
    # round the wall top: half-cylinder cap along X
    cap = cyl(8, 72, (20, 13.3, 76), axis="x")
    wall = union([wall, cap], engine="manifold")

    # Back-wall support gussets (triangular prisms approximated by rotated boxes)
    gussets = []
    for gx in (-8, 20, 48):
        g = box((6, 26, 30), (gx, 24, 20))
        g.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(-38), [1, 0, 0], point=(gx, 15, 34)))
        gussets.append(g)

    # Puck saddle: X -14..34, Y -15..15, Z 8..21.5 (puck long axis = X)
    saddle = rounded_plate(48, 30, 13.5, r=5, z0=8)
    saddle.apply_translation((10, 0, 0))

    # Guide cheeks at the bottom of the cradle (guide the shell in from above)
    cheeks = []
    for cx, sx in ((-19, 10), (42.5, 10)):  # inner faces at X=-14 and X=37.5
        cheeks.append(box((sx, 26, 24), (cx, -1, 20)))

    # Front lip: low wall that keeps the pendant from tipping forward.
    # X -14..36, Y -20..-14, Z 8..24
    lip = box((50, 6, 16), (11, -17, 16))

    dock = union([base, wall, saddle, lip] + gussets + cheeks, engine="manifold")

    cuts = []
    # Puck pocket (floor at POCKET_FLOOR_Z, open at top)
    cuts.append(box((POCKET_L, POCKET_W, 12), (10, 0, POCKET_FLOOR_Z + 6)))
    # Cable tunnel out of the saddle, +X end of the puck (cable exits puck end)
    cuts.append(box((26, 7.5, 8), (36, 0, POCKET_FLOOR_Z + 1)))
    # Cable channel across the base top to the right edge, then to the back edge
    cuts.append(box((34, 7.5, 4), (45, 0, 8.5)))
    cuts.append(box((7.5, 60, 4), (58, 18, 8.5)))
    # Cord bay clearance is structural (no wall on the left); add a cord notch
    # in the base left edge so the necklace cord can drape off the desk side
    cuts.append(box((10, 16, 10), (-62, -6, 6)))
    dock = difference([dock] + cuts, engine="manifold")
    dock = difference([dock, box((300, 300, 10), (0, 0, -5))], engine="manifold")
    return dock


# ---------------------------------------------------------------- dummy
def build_dummy():
    """Pendant silhouette (cylinder r26.9 x 16.3 + tower) in docked pose."""
    body = cyl(53.8, 16.3, (0, 0, 0), axis="y")
    tower = box((15, 10, 20), (0, 0.5, 33))
    bail = trimesh.creation.torus(major_radius=7.75, minor_radius=2.25,
                                  major_segments=32, minor_segments=12)
    bail.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    bail.apply_translation((0, 8.5, 41))
    m = union([body, tower, bail], engine="manifold")
    m = difference([m, box((24, 30, 90), (-31.5, 0, 7))], engine="manifold")  # v4 chord cut
    # docked transform: (x,y,z) -> (-z, y, x) + (10,0,48)
    T = np.eye(4)
    T[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
    T[:3, 3] = [10, 0, 48]
    m.apply_transform(T)
    return m


if __name__ == "__main__":
    os.makedirs(MODELS, exist_ok=True)
    export(build_pendant_shell_v4(), "pendant_shell_v4.stl")
    export(build_dock(), "dock.stl")
    export(build_puck_fit_test(), "puck_fit_test.stl")
    export(build_dummy(), "pendant_dummy_docked.stl")
    print("done")
