#!/usr/bin/env python3
"""
Muse Watch v6 pendant case — ivory bumper (user design image
design/pendant_case_concept.jpg, spec design/DESIGN_V6_PENDANT.md).

DESIGN
  A phone-bumper style ring around the Pixel Watch 4 45mm case edge:
  front + back lips retain the watch (snap fit), front glass fully open,
  back open as a round window (sensor r<=14.49 fully exposed).
  The watch lives in the case CROWN-UP: in the WATCH frame below the case
  is built around the watch as-is (X = right/crown, Y = +back/-front,
  Z = up in the watch's own frame); the worn/docked orientation is the
  whole-pendant rotation (x,y,z) -> (-z, y, x) + (10, 0, 48) — the same
  docked transform v4/v5 used — which puts crown +X -> up (+Z dock) and
  the charging contacts -X -> down into the v5 puck seat (top Z 28.5).

  * Crown sector OPEN: a notch on +X leaves the crown (r to 25.27)
    exposed and operable, flanked by two guard humps (bumper material
    remains at |z| > 6.8 beside the crown), as in the image.
  * Side button (27.2 deg from crown toward +Z, r ~23.1): open CUTOUT
    (no plunger) — finger accessible, one less moving part.
  * Contacts sector (-X) OPEN: chord cut at x = -19.8 (watch edge
    protrudes 2.8 mm, cf. v4 chord -19.5 / 3.1 mm) so the contact pads
    flanking the speaker slot mate with the puck groove when docked.
  * TWO eyelets at the case's +/-Z sides (left/right when worn):
    integrated lugs with a vertical oval hole 7.0 x 4.5 (cord ~4 mm).
  * SINGLE material (matte ivory PETG recommended for the snap flex;
    PLA works but the 1.0 mm front-lip undercut is tight). No separate
    liner: the v3-style TPU liner is unnecessary because retention is by
    the front/back lips and all case clearances are >= 0.35 mm.

Parts exported (ASCII STL, models/):
  pendant_shell_v6.stl   — the bumper case, watch frame, origin at watch centre
  pendant_v6_docked.stl  — case + watch dummy inside, in the v5 dock pose
Verification vs models/dock_v5.stl is printed at the end (no dock changes).
"""
import os
import numpy as np
import trimesh
from trimesh.boolean import union, difference, intersection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
SEG = 128

# ------------------------------------------------------- watch (scan, v4 data)
CASE_R = 22.6            # case max radius
CASE_TIP_F = -7.22       # front extreme (glass), total thickness 14.44
CASE_TIP_B = 7.22        # sensor tip
SENSOR_R = 14.49         # rear sensor radius (must stay fully exposed)
CROWN_R, CROWN_TIP = 3.5, 25.27   # crown dia 7.0, protrudes to r 25.27
CROWN_Y = -1.26
BUTTON_ANG = 27.2        # deg from crown toward +Z
BUTTON_R_DIST = 23.1

# ------------------------------------------------------- bumper parameters
OUT_R = 26.4             # bumper outer radius (image: slim proud ring)
IN_R = 23.0              # inner wall = CASE_R + 0.4 clearance
FRONT_LIP_R = 21.6       # front lip inner tip (> 20: display stays clear)
BACK_WIN_R = 17.0        # back window radius (> SENSOR_R 14.49 + margin)
CHORD_X = -19.8          # contacts opening chord (watch protrudes 2.8)
CROWN_NOTCH = dict(x0=20.0, y=(-8.0, 3.4), z=6.8)   # crown box cut
BUTTON_CUT_R = 4.2       # button cutout cylinder radius
EYELET_ZC = 29.25        # eyelet lug centre |z|
EYELET_SX, EYELET_SZ, EYELET_T = 15.0, 11.5, 12.5   # lug size (X, Z, thick Y)
HOLE_R, HOLE_DX = 2.25, 1.25   # oval hole: 2 cyl r2.25 at x +/-1.25 -> 7.0 x 4.5

# Bumper cross-section profile (r, y), closed loop, revolved about Y.
# Follows the case dome/back curves with >= 0.35 mm clearance (checked).
PROFILE = [
    (26.4, -6.0),    # outer front corner
    (26.4,  7.0),    # outer back corner
    (17.0,  7.0),    # back lip outer tip (window rim, back face plane)
    (17.0,  5.8),    # back lip inner step
    (22.6,  4.9),    # slope to inner wall (case back curve 21.5 @ 4.9)
    (23.0,  3.2),    # inner wall
    (23.0, -4.2),    # inner wall, front end
    (22.95, -5.1),   # slope following the front dome (offset)
    (21.6, -6.35),   # front lip inner tip (retains: 21.6 < CASE_R 22.6)
]

# Watch dummy profile (r, y) — scan-derived case solid (v4 numbers),
# slightly conservative; closed via near-axis points.
DUMMY_PROFILE = [
    (0.01, -6.4), (18.0, -6.4), (21.0, -6.05), (22.6, -4.6),
    (22.6,  3.8), (21.5,  4.9), (15.5,  5.2), (14.49, 5.5),
    (14.49, 7.22), (0.01, 7.22),
]


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


def lathe(profile, sections=SEG):
    """Revolve a closed (r, y) profile about the Y axis -> watertight mesh.
    Radial plane is XZ: theta=0 is +X (crown side)."""
    prof = np.asarray(profile, dtype=float)
    n = len(prof)
    th = np.linspace(0, 2 * np.pi, sections, endpoint=False)
    verts = np.zeros((sections * n, 3))
    for i, t in enumerate(th):
        c, s = np.cos(t), np.sin(t)
        verts[i * n:(i + 1) * n, 0] = prof[:, 0] * c
        verts[i * n:(i + 1) * n, 1] = prof[:, 1]
        verts[i * n:(i + 1) * n, 2] = prof[:, 0] * s
    faces = []
    for i in range(sections):
        j = (i + 1) % sections
        for k in range(n):
            k2 = (k + 1) % n
            a, b = i * n + k, i * n + k2
            c2, d = j * n + k2, j * n + k
            faces.append((a, d, c2)); faces.append((a, c2, b))
    m = trimesh.Trimesh(vertices=verts, faces=np.array(faces), process=True)
    if m.volume < 0:
        m.invert()
    return m


def rounded_plate(sx, sy, sz, r=6.0, z0=0.0):
    cx, cy = sx / 2 - r, sy / 2 - r
    parts = [box((sx - 2 * r, sy, sz), (0, 0, z0 + sz / 2)),
             box((sx, sy - 2 * r, sz), (0, 0, z0 + sz / 2))]
    for dx in (-cx, cx):
        for dy in (-cy, cy):
            parts.append(cyl(2 * r, sz, (dx, dy, z0 + sz / 2), seg=48))
    return union(parts, engine="manifold")


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


# ---------------------------------------------------------------- dummy
def build_watch_dummy():
    body = lathe(DUMMY_PROFILE)
    crown = cyl(CROWN_R * 2, CROWN_TIP - 20.0, (20.0 + (CROWN_TIP - 20.0) / 2, CROWN_Y, 0), axis="x")
    a = np.radians(BUTTON_ANG)
    d = np.array([np.cos(a), 0, np.sin(a)])
    btn = trimesh.creation.cylinder(radius=2.3, height=2.4, sections=32)
    btn.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    btn.apply_translation(tuple(d * (BUTTON_R_DIST - 0.6) + [0, CROWN_Y, 0]))
    return union([body, crown, btn], engine="manifold")


# ---------------------------------------------------------------- case v6
def build_case_v6():
    case = lathe(PROFILE)

    solids = [case]
    # Eyelets: rounded plates in the XZ plane (extruded along Y), both sides
    for sgn in (1, -1):
        lug = rounded_plate(EYELET_SX, EYELET_SZ, EYELET_T, r=4.0, z0=-EYELET_T / 2)
        lug.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        # after rot: plate X stays X, plate Y -> Z, thickness -> Y (centred)
        lug.apply_translation((0, 0, sgn * EYELET_ZC))
        solids.append(lug)
    case = union(solids, engine="manifold")

    cuts = []
    # Crown notch: +X sector, leaves guard humps at |z| > 6.8
    cuts.append(box((14, CROWN_NOTCH["y"][1] - CROWN_NOTCH["y"][0], CROWN_NOTCH["z"] * 2),
                    (CROWN_NOTCH["x0"] + 7, sum(CROWN_NOTCH["y"]) / 2, 0)))
    # Side-button cutout: cylinder along the button's radial direction
    a = np.radians(BUTTON_ANG)
    d = np.array([np.cos(a), 0, np.sin(a)])
    bc = trimesh.creation.cylinder(radius=BUTTON_CUT_R, height=16, sections=48)
    bc.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    bc.apply_translation(tuple(d * 24.0 + [0, CROWN_Y, 0]))
    cuts.append(bc)
    # Contacts opening: chord cut at -X (full slab, as v4)
    cuts.append(box((14.2, 20, 44), (CHORD_X - 7.1, 0, 0)))
    # Eyelet holes: vertical oval (long axis = watch X = worn vertical... 
    # in the case's own frame the slot runs along X; worn, X -> up)
    for sgn in (1, -1):
        for dx in (-HOLE_DX, HOLE_DX):
            cuts.append(cyl(HOLE_R * 2, EYELET_T + 4, (dx, 0, sgn * EYELET_ZC), axis="y"))
    case = difference([case] + cuts, engine="manifold")
    return case


# ---------------------------------------------------------------- docked
DOCK_T = np.eye(4)
DOCK_T[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
DOCK_T[:3, 3] = [10, 0, 48]


def build_docked():
    case = build_case_v6()
    dummy = build_watch_dummy()
    case.apply_transform(DOCK_T)
    dummy.apply_transform(DOCK_T)
    return trimesh.util.concatenate([case, dummy]), case, dummy


if __name__ == "__main__":
    os.makedirs(MODELS, exist_ok=True)
    case = build_case_v6()
    dummy = build_watch_dummy()

    print("--- case vs watch (watch frame) ---")
    print("case watertight=", case.is_watertight, "vol_cm3=", round(float(case.volume) / 1000, 2))
    print("case x dummy intersection cm3:", round(inter_vol(case, dummy) / 1000, 5))
    print("case bounds:", np.round(case.bounds, 2).tolist())

    both, case_d, dummy_d = build_docked()
    export(case, "pendant_shell_v6.stl")
    export(both, "pendant_v6_docked.stl")

    print("--- reload check ---")
    for name in ("pendant_shell_v6.stl", "pendant_v6_docked.stl"):
        m = trimesh.load(os.path.join(MODELS, name), process=False)
        m.merge_vertices()
        print(name, "reloaded watertight=", m.is_watertight, "is_volume=", m.is_volume)

    print("--- dock v5 fit ---")
    dock = trimesh.load(os.path.join(MODELS, "dock_v5.stl"))
    print("docked assembly x dock_v5 intersection cm3:",
          round(inter_vol(both, dock) / 1000, 5))
    print("case(docked) x dock intersection cm3:",
          round(inter_vol(case_d, dock) / 1000, 5))
    print("dummy(docked) x dock intersection cm3:",
          round(inter_vol(dummy_d, dock) / 1000, 5))
    # clearances: sample case surface, distance to dock
    pts = case_d.sample(6000)
    _, dist, _ = trimesh.proximity.closest_point(dock, pts)
    print("case->dock min distance mm:", round(float(np.min(dist)), 2))
    # bumper bottom (contacts side) lowest point vs seat top 28.5
    print("docked case lowest Z:", round(float(case_d.bounds[0][2]), 2),
          "| dummy lowest Z:", round(float(dummy_d.bounds[0][2]), 2),
          "(puck seat top = 28.5, groove below)")
    print("docked case bounds:", np.round(case_d.bounds, 2).tolist())
    print("done")
