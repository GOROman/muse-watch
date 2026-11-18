#!/usr/bin/env python3
"""
Muse Watch v7 dock — compact trapezoid tower (user design image
design/dock_concept_v7.jpg, spec design/DESIGN_V7_DOCK.md).

FORM (new vs v5's wide tray):
  * Compact TRAPEZOID tower, ivory: 100 x 76 footprint (v5: 124 x 92),
    height 66 (v5: 80). Sloped flanks (hull-tapered front wedge + back
    wall), flat near-vertical front face, tall back wall forming the
    cradle, rounded plates (r >= 6) throughout.
  * Cradle: flat seat at Z 28.5 in front of the back wall (front face
    Y 9.3, exactly as v5) + TWO VERTICAL GUIDE FINS flanking the v6 case
    (3 mm plates, inner faces 1.1 mm clear of the bumper, tops Z 50).
    Each fin has a SLOT (Y +-7.5, Z 39.5..52.5) so the case's eyelets —
    the only parts reaching past the fins — drop straight through when
    docking. Crown notch dips the wall top to Z 61 around X 10 (the
    crown itself is in front of the wall; clearance 6.9 mm, measured).
  * Orange accent is now a RECTANGULAR BADGE (26 x 12 x 3, separate STL)
    in a shallow pocket on the front face, lower right, proud by 1.8 mm.
  * 6 horizontal rib slits low on BOTH flanks.
  * Cord: NO channel cut — at eyelet height the only dock material near
    the cord's Y band (+-6.25) is the left fin, which is slotted for the
    eyelet; beyond it the flank is open air (the back wall is at Y >= 9.3,
    behind the cord), so the cord drapes straight off the left side,
    as in the concept photo.

MECHANISM — UNCHANGED from the verified v4/v5/v6 set (hard constraints):
  puck cavity 42.6 x 28.4 @ CX 10, puck bottom Z 18.9, seat top Z 28.5,
  aperture 41.6 x 27.6 exposing only the puck's oval face, puck inserted
  from the bottom on the v5 cover plate (models/puck_cover.stl is REUSED
  unchanged — recess, shaft, rails and M3 pilots are identical, so no
  puck_cover_v7.stl is produced). Cable: v5 tunnel cross-section
  (7.5 x 8) out of the puck's +X end, then a channel turning to the BACK,
  exiting the rear face at the right (concept photo: cable out the back /
  right-back). Pendant docked pose/transform identical; verified
  interference 0 vs pendant_v6_docked (case + watch dummy).

Parts exported (ASCII STL, models/):
  dock_v7.stl, accent_badge.stl (fitted position, separate part).
"""
import os
import sys
import numpy as np
import trimesh
from trimesh.boolean import union, difference, intersection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
SEG = 96
sys.path.insert(0, HERE)

# ------------------------------------------------- v5 functional constants
# Puck / pocket — DO NOT CHANGE (verified v4/v5/v6 mating geometry)
PUCK_L, PUCK_W, PUCK_H = 41.0, 27.0, 9.6
POCKET_L, POCKET_W = 42.6, 28.4
POCKET_FLOOR_Z = 18.9
PUCK_TOP_Z = POCKET_FLOOR_Z + PUCK_H            # 28.5 seat plane
PUCK_CX = 10.0
APERTURE_L, APERTURE_W = PUCK_L + 0.6, PUCK_W + 0.6
COVER_SX, COVER_SY = 58.0, 44.0                 # v5 cover plate (reused)
RECESS_CLEAR = 0.4
SCREW_XS = (-14.5, 34.5)                        # v5 M3 pilot positions
SCREW_PILOT_D = 2.5
TUNNEL = ((26, 7.5, 8), (36, 0, POCKET_FLOOR_Z + 1))   # v5, out of puck +X end
CHANNEL_BACK = ((7.5, 46, 8), (44, 16, POCKET_FLOOR_Z + 1))  # turn to the back

# ------------------------------------------------- v7 body (styling)
BASE_SX, BASE_SY, BASE_T, BASE_R = 100.0, 76.0, 10.0, 12.0
BASE_C = (5.0, -1.0)                            # footprint X -45..55, Y -39..37
SEAT_SX, SEAT_SY, SEAT_R = 84.0, 30.0, 8.0      # seat core, top = 28.5
SEAT_C = (10.0, -1.0)                           # X -32..52, Y -16..14
# Front wedge = hull of two plates (front Y -39 vertical to Z 18, then
# sloping back to -33 at Z 37; back edge -5 -> -9 keeps >= 0.85 mm clear
# of the watch dummy's front curve above the seat)
WEDGE_B = (90.0, 34.0, 10.0, 8.0, 8.0, (5.0, -22.0))   # sx, sy, sz, r, z0, c
WEDGE_T = (82.0, 24.0, 19.0, 8.0, 18.0, (5.0, -21.0))  # front -33, back -9
# Back wall = hull of two plates, front face flat at Y 9.3 (as v5)
WALL_B = (80.0, 24.0, 26.0, 8.0, 8.0, (9.0, 21.3))     # Y 9.3..33.3, Z 8..34
WALL_T = (72.0, 19.0, 32.0, 7.0, 34.0, (9.0, 18.8))    # Y 9.3..28.3, Z 34..66
WALL_TOP_Z = 66.0
CROWN_NOTCH = ((18, 28, 31), (10, 22, 76.5))    # wall top -> Z 61 @ X 1..19
FLANK_L = (14.0, 52.0, 16.0, 6.0, 8.0, (-38.0, -2.0))  # X -45..-31, Z 8..24
FLANK_R = (12.0, 52.0, 16.0, 6.0, 8.0, (49.0, -2.0))   # X 43..55, Z 8..24
# Guide fins: YZ-profile plates, 3 mm thick in X
FIN_X = (-20.5, 37.5)                           # left/right fin inner X start
FIN_PROFILE = [(-12, 28.5), (12, 28.5), (12, 50), (-4, 50), (-12, 41)]
FIN_NOTCH = ((7, 15, 13), None)                 # eyelet slot, per-fin centre
# Rib slits on both flanks
RIB_ZS = (4.0, 7.0, 10.0, 13.0, 16.0, 19.0)
RIB_BOX = (12, 58, 1.3)
# Orange badge (front face, lower right) + its pocket
BADGE_SX, BADGE_SY, BADGE_T, BADGE_R = 26.0, 12.0, 3.0, 5.0
BADGE_C = (28.0, -39.3, 12.0)                   # back on pocket floor -37.8
BADGE_POCKET = ((27.5, 1.2, 13.5), (28.0, -38.4, 12.0))


# ---------------------------------------------------------------- helpers
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
    """Box with vertical corners rounded (same helper as build_v5)."""
    cx, cy = sx / 2 - r, sy / 2 - r
    parts = []
    if sx - 2 * r > 0:
        parts.append(box((sx - 2 * r, sy, sz), (0, 0, z0 + sz / 2)))
    if sy - 2 * r > 0:
        parts.append(box((sx, sy - 2 * r, sz), (0, 0, z0 + sz / 2)))
    seen = set()
    for dx in (-cx, cx):
        for dy in (-cy, cy):
            key = (round(dx, 6), round(dy, 6))
            if key not in seen:
                seen.add(key)
                parts.append(cyl(2 * r, sz, (dx, dy, z0 + sz / 2), seg=48))
    return union(parts, engine="manifold")


def plate(spec):
    sx, sy, sz, r, z0, c = spec
    m = rounded_plate(sx, sy, sz, r=r, z0=z0)
    m.apply_translation((c[0], c[1], 0))
    return m


def hull2(a, b):
    return trimesh.util.concatenate([a, b]).convex_hull


def build_fin(x0):
    """Guide fin: FIN_PROFILE in (Y, Z) (convex), extruded 3 mm along X
    from x0. Built as a manual prism — no shapely in this environment."""
    prof = np.asarray(FIN_PROFILE, dtype=float)          # (Y, Z) points
    n = len(prof)
    verts = []
    for x in (x0, x0 + 3.0):
        for (y, z) in prof:
            verts.append((x, y, z))
    faces = []
    for i in range(1, n - 1):                            # caps (fan)
        faces.append((0, i + 1, i))                      # x0 cap (normal -X)
        faces.append((n, n + i, n + i + 1))              # x1 cap (normal +X)
    for i in range(n):                                   # side quads
        j = (i + 1) % n
        faces.append((i, j, n + j))
        faces.append((i, n + j, n + i))
    m = trimesh.Trimesh(vertices=np.array(verts), faces=np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


def export(mesh, name):
    path = os.path.join(MODELS, name)
    trimesh.exchange.export.export_mesh(mesh, path, file_type="stl_ascii")
    print(name, "watertight=", mesh.is_watertight,
          "vol_cm3=", round(float(mesh.volume) / 1000, 2),
          "bounds=", np.round(mesh.bounds, 1).tolist())
    return path


def inter_vol(a, b):
    m = intersection([a, b], engine="manifold")
    return 0.0 if m is None else float(m.volume)


# ---------------------------------------------------------------- dock
def build_dock_v7():
    solids = []
    # Base plate (flat bottom, r12 corners)
    base = rounded_plate(BASE_SX, BASE_SY, BASE_T, r=BASE_R, z0=0)
    base.apply_translation((BASE_C[0], BASE_C[1], 0))
    solids.append(base)
    # Seat core: top = seat plane 28.5, carries the aperture frame
    seat = rounded_plate(SEAT_SX, SEAT_SY, PUCK_TOP_Z - 8, r=SEAT_R, z0=8)
    seat.apply_translation((SEAT_C[0], SEAT_C[1], 0))
    solids.append(seat)
    # Front wedge (trapezoid front) and back wall (cradle), hull-tapered
    solids.append(hull2(plate(WEDGE_B), plate(WEDGE_T)))
    solids.append(hull2(plate(WALL_B), plate(WALL_T)))
    # Flank blocks (trapezoid shoulders below the seat)
    solids.append(plate(FLANK_L))
    solids.append(plate(FLANK_R))
    # Guide fins
    for x0 in FIN_X:
        solids.append(build_fin(x0))

    dock = union(solids, engine="manifold")

    # ---- functional cuts (v5 numbers; puck/seat/cable geometry unchanged)
    cuts = [
        # puck cavity + bottom insertion shaft (to underside of aperture frame)
        box((POCKET_L, POCKET_W, 28.0), (PUCK_CX, 0, 12.9)),          # Z -1.1..26.9
        # seat aperture: only the puck's grooved top face shows, flush 28.5
        box((APERTURE_L, APERTURE_W, 4), (PUCK_CX, 0, PUCK_TOP_Z + 0.4)),
        # bottom recess for the (reused v5) cover plate
        box((COVER_SX + RECESS_CLEAR, COVER_SY + RECESS_CLEAR, 2.8), (PUCK_CX, 0, 1.2)),
        # cable path: v5 tunnel out of the puck +X end, then back
        box(*TUNNEL), box(*CHANNEL_BACK),
        # crown notch in the back-wall top edge
        box(*CROWN_NOTCH),
        # badge pocket on the front face
        box(*BADGE_POCKET),
    ]
    # M3 pilot holes in the dock body (v5 positions, beside the shaft)
    for sx in SCREW_XS:
        cuts.append(cyl(SCREW_PILOT_D, 7.5, (sx, 0, 2.0)))
    # eyelet slots through both fins
    for x0 in FIN_X:
        cuts.append(box(FIN_NOTCH[0], (x0 + 1.5, 0, 46.0)))
    dock = difference([dock] + cuts, engine="manifold")

    # ---- styling cuts: rib slits low on both flanks
    ribs = []
    for zc in RIB_ZS:
        ribs.append(box(RIB_BOX, (-46.5, -2.0, zc)))
        ribs.append(box(RIB_BOX, (56.5, -2.0, zc)))
    dock = difference([dock] + ribs, engine="manifold")

    # flat bottom (v5 trim)
    dock = difference([dock, box((300, 300, 10), (0, 0, -5))], engine="manifold")
    return dock


# ---------------------------------------------------------------- badge
def build_accent_badge():
    """Rounded-rect orange badge, exported in FITTED position: back face
    on the pocket floor (Y -37.8), front proud of the front face by 1.8."""
    badge = rounded_plate(BADGE_SX, BADGE_SY, BADGE_T, r=BADGE_R, z0=-BADGE_T / 2)
    # plate is (X, Y=height, Z=thickness); rotate +90 deg about X so the
    # height runs along Z and the thickness along Y
    badge.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    badge.apply_translation(BADGE_C)
    return badge


def build_puck_proxy():
    return box((PUCK_L, PUCK_W, PUCK_H), (PUCK_CX, 0, POCKET_FLOOR_Z + PUCK_H / 2))


if __name__ == "__main__":
    os.makedirs(MODELS, exist_ok=True)
    dock = build_dock_v7()
    badge = build_accent_badge()
    puck = build_puck_proxy()
    cover = trimesh.load(os.path.join(MODELS, "puck_cover.stl"))  # v5, reused

    import build_v6
    _, case_d, dummy_d = build_v6.build_docked()

    print("--- in-memory verification ---")
    for n, m in [("dock_v7", dock), ("badge", badge)]:
        print(n, "watertight=", m.is_watertight, "vol_cm3=", round(float(m.volume) / 1000, 2))
    print("dock_v7 envelope mm:", np.round(dock.bounds[1] - dock.bounds[0], 1).tolist(),
          "bounds:", np.round(dock.bounds, 1).tolist())

    assert (POCKET_L, POCKET_W, POCKET_FLOOR_Z) == (42.6, 28.4, 18.9)
    assert PUCK_TOP_Z == 28.5
    shaft = box((POCKET_L, POCKET_W, PUCK_TOP_Z - 1.6),
                (PUCK_CX, 0, (PUCK_TOP_Z - 1.6) / 2))
    print("shaft prism (pocket section, Z 0..26.9) x dock mm3:", round(inter_vol(shaft, dock), 3))
    print("dock x case_v6(docked) intersection cm3:", round(inter_vol(dock, case_d) / 1000, 5))
    print("dock x watch dummy(docked) intersection cm3:", round(inter_vol(dock, dummy_d) / 1000, 5))
    print("dock x puck proxy intersection mm3:", round(inter_vol(dock, puck), 3))
    print("dock x v5 cover (fitted) intersection mm3:", round(inter_vol(dock, cover), 3))
    print("cover x puck proxy intersection mm3:", round(inter_vol(cover, puck), 3))
    print("badge x dock intersection mm3:", round(inter_vol(badge, dock), 3),
          "(0 = sits in pocket, touching floor)")
    # seat plane probe: ring around the aperture must be solid at Z 28.4
    # (seat top = 28.5) and the aperture column must be open
    ring = [(x, y, 28.4) for x in np.linspace(-14, 34, 13) for y in (-16.5, 15.5)]
    ring += [(x, y, 28.4) for y in np.linspace(-12, 12, 9) for x in (-13.5, 33.5)]
    print("seat ring solid at Z 28.4:", int(dock.contains(np.array(ring)).sum()), "/", len(ring))
    col = dock.contains(np.array([(10, 0, 27.5), (10, 0, 28.4), (10, 0, 29.5)]))
    print("aperture centre column open (expect all False):", col.tolist())
    # crown envelope (dock frame: axis Z at (10,-1.26), d7.4, Z 67..74)
    crown = cyl(7.4, 7.0, (10, -1.26, 70.5))
    print("crown envelope x dock mm3:", round(inter_vol(crown, dock), 3))
    pts = crown.sample(1200)
    _, dist, _ = trimesh.proximity.closest_point(dock, pts)
    print("crown envelope min distance to dock mm:", round(float(np.min(dist)), 2), "(need >= 5)")
    # fin-to-case clearance (sampled, both fins' inner faces are X planes)
    cpts = case_d.sample(8000)
    _, cdist, _ = trimesh.proximity.closest_point(dock, cpts)
    print("case -> dock min distance mm:", round(float(np.min(cdist)), 2))

    print("--- exports ---")
    export(dock, "dock_v7.stl")
    export(badge, "accent_badge.stl")

    print("--- reload check (ASCII round-trip) ---")
    for name in ("dock_v7.stl", "accent_badge.stl"):
        m = trimesh.load(os.path.join(MODELS, name), process=False)
        m.merge_vertices()
        print(name, "reloaded watertight=", m.is_watertight, "is_volume=", m.is_volume)
    print("done")
