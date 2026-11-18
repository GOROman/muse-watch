#!/usr/bin/env python3
"""
Muse Watch v5 dock — v4 mechanism, retro styling, puck fully embedded.

MECHANISM (unchanged from v4, src/build_muse_watch.py; confirmed by the
user's real-unit photo design/charging_orientation.jpg):
  Pendant rotated 90 deg CCW in its plane: charging (left) edge DOWN,
  crown UP, tower + necklace cord to the LEFT. The official puck lies FLAT
  in the dock; the watch's protruding left edge (shell chord cut -19.5,
  protrusion 3.1 mm) drops into the puck groove; gravity + magnet mate it.

  Docked transform of pendant point (x, y, z) -> (-z, y, x) + (10, 0, 48).
  Frames: X = left(-) / right(+), Y = front(-) / back(+), Z = up. mm.

WHAT CHANGED vs v4 (styling + puck embedding only — no functional move):
  * Chunky rounded ivory body: base corner radius 10, seat block r6,
    back wall thickened to 10 mm with a rolled top and vertical rib grooves,
    ribbed band (3 grooves) around the base, ribbed front lip.
  * Puck is EMBEDDED: internal cavity + insertion shaft from the bottom,
    only the puck's grooved top face exposed through an aperture in the
    seat, flush at Z = PUCK_TOP_Z (28.5 = v4 pocket floor 18.9 + puck 9.6).
  * Puck stays replaceable: it rides on the rails of a separate bottom
    cover plate (models/puck_cover.stl) and is held by 2x M3x6 screws
    (pilots in the dock body). No glue, no tape.
  * Orange accent disc (separate STL) on the right cheek's outer face,
    clear of the cable tunnel exit.
  * Left cord bay stays OPEN; cord notch stays; back wall only where v4
    has it (right portion); all v4 cable cuts are byte-identical numbers.

Parts exported (ASCII STL, models/):
  dock_v5.stl, accent_disc.stl, puck_cover.stl, pendant_dummy_v5_docked.stl
  (dummy = the real v4 shell mesh in the v4 docked pose, fit check only).
"""
import os
import numpy as np
import trimesh
from trimesh.boolean import union, difference, intersection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
SEG = 96

# ---------------------------------------------------------------- parameters
# Puck / pocket — v4 functional dimensions, DO NOT CHANGE
PUCK_L, PUCK_W, PUCK_H = 41.0, 27.0, 9.6        # official puck (Google specs)
POCKET_L, POCKET_W = 42.6, 28.4                 # v4 pocket = v5 cavity/shaft
POCKET_FLOOR_Z = 18.9                           # v4 pocket floor = puck bottom Z
PUCK_TOP_Z = POCKET_FLOOR_Z + PUCK_H            # 28.5, flush seat height
PUCK_CX = 10.0                                  # pocket centre X (v4)
SHELL_CUT_X = -19.5                             # v4 shell chord cut (pendant frame)

# Embedded-puck aperture in the seat top (puck outline + 0.3/side; the frame
# ring hides the cavity gap and keeps the groove fully unobstructed)
APERTURE_L, APERTURE_W = PUCK_L + 0.6, PUCK_W + 0.6
APERTURE_FRAME_T = 1.6                          # frame spans Z 26.9..28.5

# Body (styling)
BASE_SX, BASE_SY, BASE_T, BASE_R = 124.0, 92.0, 8.0, 10.0
SEAT_SX, SEAT_SY, SEAT_R = 52.0, 34.0, 6.0      # centred (10, 0), top = 28.5
BAND_GROOVES = 3
BAND_GROOVE_DEPTH, BAND_GROOVE_H = 1.3, 1.4
BAND_GROOVE_ZS = (2.0, 4.1, 6.2)                # groove centre heights on base
WALL_X0, WALL_X1 = -16.0, 56.0                  # v4 wall span (right portion)
WALL_FRONT_Y, WALL_T = 9.3, 10.0                # front face = v4, thickened back
WALL_TOP_Z = 75.0                               # + r5 roll -> top at 80 (v4: 80)
WALL_RIB_W, WALL_RIB_DEPTH, WALL_RIB_PITCH = 2.2, 1.2, 8.0
CHEEK_L = (-19.0, -1.0)                         # centre; face planes = v4
CHEEK_R = (43.5, -6.5)                          # extended block (disc face)
LIP_GROOVE_ZS = (12.5, 16.5, 20.5)

# Accent disc (right cheek outer face, clear of the cable tunnel exit)
DISC_R, DISC_T = 9.0, 3.0
DISC_POS = (51.0, -12.0, 30.0)                  # centre; back face at X = 49.5

# Bottom cover plate + puck insertion (from below)
COVER_SX, COVER_SY, COVER_T, COVER_R = 58.0, 44.0, 2.6, 6.0
RECESS_CLEAR = 0.4                              # recess = cover + 0.4 total/side*2
RAIL_Y, RAIL_W, RAIL_SX = 10.5, 4.0, 40.0       # rails carry the puck bottom
SCREW_XS = (-14.5, 34.5)                        # 2x M3x6, pilots in dock body
SCREW_PILOT_D, SCREW_CLEAR_D = 2.5, 3.4

# v4 cable cuts — identical numbers to build_muse_watch.py
TUNNEL = ((26, 7.5, 8), (36, 0, POCKET_FLOOR_Z + 1))       # out of puck +X end
CHANNEL_A = ((34, 7.5, 4), (45, 0, 8.5))                    # across base top
CHANNEL_B = ((7.5, 60, 4), (58, 18, 8.5))                   # to the back edge
CORD_NOTCH = ((10, 16, 10), (-62, -6, 6))                   # base left edge


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
    """Box with vertical corners rounded (union of box + 4 corner cylinders)."""
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


def export(mesh, name):
    path = os.path.join(MODELS, name)
    trimesh.exchange.export.export_mesh(mesh, path, file_type="stl_ascii")
    print(name, "watertight=", mesh.is_watertight,
          "vol_cm3=", round(float(mesh.volume) / 1000, 2),
          "bounds=", np.round(mesh.bounds, 1).tolist())
    return path


# ---------------------------------------------------------------- dock
def build_dock_v5():
    solids = []
    # Base plate 124 x 92 x 8, chunky r10 corners (v4 footprint kept)
    solids.append(rounded_plate(BASE_SX, BASE_SY, BASE_T, r=BASE_R, z0=0))

    # Seat block around the embedded puck: top = seat plane Z 28.5
    seat = rounded_plate(SEAT_SX, SEAT_SY, PUCK_TOP_Z - 6, r=SEAT_R, z0=6)
    seat.apply_translation((PUCK_CX, 0, 0))
    solids.append(seat)

    # Back wall (right portion only, as v4): front face stays at Y 9.3,
    # thickened to 10 mm, rolled top (r5 half-cylinder) reaching Z 80
    wall_h = WALL_TOP_Z - 6
    solids.append(box((WALL_X1 - WALL_X0, WALL_T, wall_h),
                      ((WALL_X0 + WALL_X1) / 2, WALL_FRONT_Y + WALL_T / 2, 6 + wall_h / 2)))
    solids.append(cyl(WALL_T, WALL_X1 - WALL_X0,
                      ((WALL_X0 + WALL_X1) / 2, WALL_FRONT_Y + WALL_T / 2, WALL_TOP_Z), axis="x"))

    # v4 gussets behind the wall — same boxes/rotation, but clipped to
    # Y >= WALL_FRONT_Y: as drawn in v4 their rotated front corners swing
    # forward of the wall face and clip the shell's back rim (~4.6 mm3,
    # verified against the v4 build). Clipping keeps them purely behind
    # the wall; no functional dimension is affected.
    for gx in (-8, 20, 48):
        g = box((6, 26, 30), (gx, 24, 20))
        g.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(-38), [1, 0, 0], point=(gx, 15, 34)))
        g = difference([g, box((80, 30, 95), (20, WALL_FRONT_Y - 15, 40))],
                       engine="manifold")
        solids.append(g)

    # Guide cheeks: inner faces exactly where v4 has them (X -14 / +37.5)
    cheek_l = rounded_plate(10, 26, 26, r=4, z0=6)
    cheek_l.apply_translation(CHEEK_L + (0,))
    solids.append(cheek_l)
    # Right cheek is an extended chunky block so its outer face can carry
    # the accent disc clear of the cable tunnel exit (Y +-3.75, Z 15.9..23.9)
    cheek_r = rounded_plate(12, 39, 34, r=5, z0=6)
    cheek_r.apply_translation(CHEEK_R + (0,))
    solids.append(cheek_r)

    # Front lip (v4 position; taller + rounded for the retro front ribs)
    lip = rounded_plate(50, 6, 21, r=3, z0=6)
    lip.apply_translation((11, -17, 0))
    solids.append(lip)

    dock = union(solids, engine="manifold")

    # ---- functional cuts (v4 numbers; puck/seat/cable geometry unchanged)
    cuts = [
        # puck cavity + bottom insertion shaft: pocket cross-section from
        # below the base up to the underside of the seat aperture frame
        box((POCKET_L, POCKET_W, 28.0), (PUCK_CX, 0, 12.9)),          # Z -1.1..26.9
        # seat aperture: only the puck's grooved top face shows, flush 28.5
        box((APERTURE_L, APERTURE_W, 4), (PUCK_CX, 0, PUCK_TOP_Z + 0.4)),
        # bottom recess for the cover plate
        box((COVER_SX + RECESS_CLEAR, COVER_SY + RECESS_CLEAR, 2.8), (PUCK_CX, 0, 1.2)),
        # cable path, v4 verbatim
        box(*TUNNEL), box(*CHANNEL_A), box(*CHANNEL_B),
        # cord notch in the base left edge, v4 verbatim
        box(*CORD_NOTCH),
    ]
    # M3 pilot holes in the dock body (material above the recess floor)
    for sx in SCREW_XS:
        cuts.append(cyl(SCREW_PILOT_D, 7.5, (sx, 0, 2.0)))
    dock = difference([dock] + cuts, engine="manifold")

    # ---- styling cuts: ribbed band, wall ribs, lip ribs
    style = []
    for zc in BAND_GROOVE_ZS[:BAND_GROOVES]:
        outer = rounded_plate(BASE_SX, BASE_SY, BAND_GROOVE_H, r=BASE_R, z0=zc - BAND_GROOVE_H / 2)
        inner = rounded_plate(BASE_SX - 2 * BAND_GROOVE_DEPTH, BASE_SY - 2 * BAND_GROOVE_DEPTH,
                              BAND_GROOVE_H, r=BASE_R - BAND_GROOVE_DEPTH, z0=zc - BAND_GROOVE_H / 2)
        style.append(difference([outer, inner], engine="manifold"))
    x = -12.0
    while x <= 52.0:  # vertical rib grooves on the back-wall front face
        style.append(box((WALL_RIB_W, 2.5, 62), (x, WALL_FRONT_Y - 0.05, 43)))
        x += WALL_RIB_PITCH
    for zc in LIP_GROOVE_ZS:  # horizontal ribs on the front lip face
        style.append(box((46, 2.0, 1.3), (11, -19.6, zc)))
    dock = difference([dock] + style, engine="manifold")

    # flat bottom (v4 trim)
    dock = difference([dock, box((300, 300, 10), (0, 0, -5))], engine="manifold")
    return dock


# ---------------------------------------------------------------- disc
def build_accent_disc():
    disc = cyl(DISC_R * 2, DISC_T, DISC_POS, axis="x")
    hole = cyl(3.2, DISC_T + 2, DISC_POS, axis="x")  # optional M3 / pin hole
    return difference([disc, hole], engine="manifold")


# ---------------------------------------------------------------- cover
def build_puck_cover():
    """Bottom cover plate + puck rails, exported in FITTED dock coordinates.
    Assembly: puck rests on the rails (tops at POCKET_FLOOR_Z), cable is fed
    into the tunnel, the whole cover slides up the shaft from below and is
    screwed in with 2x M3x6. Puck removal = reverse."""
    plate = rounded_plate(COVER_SX, COVER_SY, COVER_T, r=COVER_R, z0=0)
    plate.apply_translation((PUCK_CX, 0, 0))
    rails = [box((RAIL_SX, RAIL_W, POCKET_FLOOR_Z - COVER_T),
                 (PUCK_CX, RAIL_Y, (COVER_T + POCKET_FLOOR_Z) / 2)),
             box((RAIL_SX, RAIL_W, POCKET_FLOOR_Z - COVER_T),
                 (PUCK_CX, -RAIL_Y, (COVER_T + POCKET_FLOOR_Z) / 2))]
    cover = union([plate] + rails, engine="manifold")
    holes = [cyl(SCREW_CLEAR_D, COVER_T + 2.4, (sx, 0, COVER_T / 2)) for sx in SCREW_XS]
    return difference([cover] + holes, engine="manifold")


# ---------------------------------------------------------------- dummy
def build_dummy_v5():
    """The real v4 shell (chord cut -19.5) in the v4 docked pose."""
    shell = trimesh.load(os.path.join(MODELS, "pendant_shell_v4.stl"))
    T = np.eye(4)
    T[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
    T[:3, 3] = [10, 0, 48]
    shell.apply_transform(T)
    return shell


def build_puck_proxy():
    """Official puck as a plain box at its seated position (check only)."""
    return box((PUCK_L, PUCK_W, PUCK_H), (PUCK_CX, 0, POCKET_FLOOR_Z + PUCK_H / 2))


def inter_vol(a, b):
    m = intersection([a, b], engine="manifold")
    return 0.0 if m is None else float(m.volume)


if __name__ == "__main__":
    os.makedirs(MODELS, exist_ok=True)
    dock = build_dock_v5()
    disc = build_accent_disc()
    cover = build_puck_cover()
    dummy = build_dummy_v5()
    puck = build_puck_proxy()

    print("--- in-memory verification ---")
    for n, m in [("dock", dock), ("disc", disc), ("cover", cover), ("dummy", dummy)]:
        print(n, "watertight=", m.is_watertight, "vol_cm3=", round(float(m.volume) / 1000, 2))

    # functional dimensions identical to v4 (asserted in code)
    assert (POCKET_L, POCKET_W, POCKET_FLOOR_Z) == (42.6, 28.4, 18.9)
    assert PUCK_TOP_Z == 28.5
    shaft = box((POCKET_L, POCKET_W, PUCK_TOP_Z - APERTURE_FRAME_T),
                (PUCK_CX, 0, (PUCK_TOP_Z - APERTURE_FRAME_T) / 2))
    print("shaft prism (pocket section, Z 0..26.9) x dock mm3:", round(inter_vol(shaft, dock), 3))
    print("dock x dummy(shell) intersection cm3:", round(inter_vol(dock, dummy) / 1000, 4))
    print("dock x puck proxy intersection mm3:", round(inter_vol(dock, puck), 3))
    print("dock x cover(fitted) intersection mm3:", round(inter_vol(dock, cover), 3))
    print("cover x puck proxy intersection mm3:", round(inter_vol(cover, puck), 3))
    verts = dock.vertices
    sel = verts[(verts[:, 0] > -13) & (verts[:, 0] < 33) & (verts[:, 1] > -17) & (verts[:, 1] < -5)]
    print("seat top Z (front seat region):", round(float(sel[:, 2].max()), 2), "(expect 28.5)")
    # crown envelope (dock frame: axis Z at (10,-1.26), r3.5, Z 69..77.5)
    crown = cyl(7.0, 8.5, (10, -1.26, 73.25))
    print("crown envelope x dock mm3:", round(inter_vol(crown, dock), 3))
    pts = crown.sample(800)
    _, dist, _ = trimesh.proximity.closest_point(dock, pts)
    print("crown envelope min distance to dock mm:", round(float(np.min(dist)), 2))

    print("--- exports ---")
    export(dock, "dock_v5.stl")
    export(disc, "accent_disc.stl")
    export(cover, "puck_cover.stl")
    export(dummy, "pendant_dummy_v5_docked.stl")

    print("--- reload check (ASCII round-trip) ---")
    for name in ("dock_v5.stl", "accent_disc.stl", "puck_cover.stl", "pendant_dummy_v5_docked.stl"):
        m = trimesh.load(os.path.join(MODELS, name), process=False)
        m.merge_vertices()
        print(name, "reloaded watertight=", m.is_watertight, "is_volume=", m.is_volume)
    print("done")
