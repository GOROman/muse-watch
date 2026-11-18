#!/usr/bin/env python3
"""
Muse Watch — rigorous puck-fit verification for dock v7 + fit-test slice.

Checks (all manifold booleans against the SHIPPED models/dock_v7.stl):
  1. Realistic puck proxy: true stadium prism 41.0 x 27.0 x 9.6
     (corner radius 13.5 = half the short side) + cable stub d3.5 x 30
     exiting the +X short end at mid height. (build_v5/v7 used a plain
     BOX proxy; the stadium is inscribed in that box, so this is the
     realistic, slightly looser solid.)
  2. Bottom-insertion simulation: puck translated straight down from its
     seated pose in 2 mm steps to fully below the dock; intersection
     volume with the dock at every step (body-only, and body+rigid-stub
     for the record — the real cable flexes and is fed through the
     tunnel during assembly, it does not translate rigidly).
  3. Final-pose clearances: puck x dock, puck x cover (fitted), wall gaps.
  4. Cable route: stub + segmented bend down into the v7 tunnel, along
     it, then the back channel out the rear face; per-segment and total
     intersection with the dock.
  5. Aperture exposure: puck top-face groove zone (stadium inset 4 mm)
     vs the 41.6 x 27.6 seat aperture footprint — margins.
  6. Fit-test piece: models/puck_fit_test_v7.stl = dock_v7 ∩ slab
     Z 0..34 (the literal bottom slice of the production dock). Verified
     watertight after ASCII reload, puck seats in it with 0 intersection
     and identical gaps; its mate is the existing models/puck_cover.stl.

Run: /tmp/mw-venv/bin/python src/verify_puck_fit_v7.py
"""
import os
import numpy as np
import trimesh
from trimesh.boolean import union, difference, intersection

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")
SEG = 96

# ---- dock-frame constants (from build_v7.py; do not change) ----
PUCK_L, PUCK_W, PUCK_H = 41.0, 27.0, 9.6
POCKET_L, POCKET_W = 42.6, 28.4
POCKET_FLOOR_Z = 18.9
PUCK_TOP_Z = POCKET_FLOOR_Z + PUCK_H            # 28.5
PUCK_CX = 10.0
APERTURE_L, APERTURE_W = 41.6, 27.6
CABLE_D = 3.5


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


def inter(a, b):
    m = intersection([a, b], engine="manifold")
    if m is None:
        return 0.0, None
    return float(m.volume), m


def load(name):
    m = trimesh.load(os.path.join(MODELS, name), process=False)
    if isinstance(m, trimesh.Scene):
        m = m.dump(concatenate=True)
    m.merge_vertices()
    return m


# ---------------------------------------------------------------- puck proxy
def build_puck_body(cx=PUCK_CX, z_bot=POCKET_FLOOR_Z):
    """True stadium prism: central box + two r13.5 end cylinders."""
    r = PUCK_W / 2.0
    straight = PUCK_L - PUCK_W                    # 14.0
    zc = z_bot + PUCK_H / 2
    parts = [box((straight, PUCK_W, PUCK_H), (cx, 0, zc))]
    for dx in (-straight / 2, straight / 2):
        parts.append(cyl(PUCK_W, PUCK_H, (cx + dx, 0, zc), seg=SEG))
    return union(parts, engine="manifold")


def build_cable_stub(body_cx=PUCK_CX, z_bot=POCKET_FLOOR_Z):
    """d3.5 stub, 30 mm long, out of the +X short end at puck mid height."""
    zc = z_bot + PUCK_H / 2                       # 23.7
    x0 = body_cx + PUCK_L / 2                     # 30.5 puck face
    return cyl(CABLE_D, 30.0, (x0 + 15.0, 0, zc), axis="x")


def seg_cyl(p0, p1, d=CABLE_D):
    """Cylinder between two points (for the routed-cable model)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    v = p1 - p0
    L = float(np.linalg.norm(v))
    m = trimesh.creation.cylinder(radius=d / 2, height=L, sections=48)
    z = np.array([0, 0, 1.0])
    axis = np.cross(z, v / L)
    if np.linalg.norm(axis) < 1e-9:
        T = np.eye(4)
    else:
        ang = np.arccos(np.clip(np.dot(z, v / L), -1, 1))
        T = trimesh.transformations.rotation_matrix(ang, axis)
    m.apply_transform(T)
    m.apply_translation((p0 + p1) / 2)
    return m


# routed cable: stub at puck mid height, segmented bend down into the
# tunnel (tunnel void: X 23..49, Y +-3.75, Z 15.9..23.9), along it to
# X 44, then the back channel (X 40.25..47.75, Z 15.9..23.9) out the
# rear face (Y 37).
CABLE_PTS = [
    (28.5, 0, 23.7), (31.0, 0, 23.55), (32.2, 0, 22.7), (33.6, 0, 21.3),
    (35.4, 0, 20.2), (38.0, 0, 19.9), (44.0, 0, 19.9),
    (44.0, 10.0, 19.9), (44.0, 42.0, 19.9),
]


def build_routed_cable():
    parts = []
    for a, b in zip(CABLE_PTS[:-1], CABLE_PTS[1:]):
        parts.append(seg_cyl(a, b))
    for p in CABLE_PTS[1:-1]:
        s = trimesh.creation.icosphere(subdivisions=3, radius=CABLE_D / 2)
        s.apply_translation(p)
        parts.append(s)
    return union(parts, engine="manifold")


def main():
    dock = load("dock_v7.stl")
    cover = load("puck_cover.stl")
    print("dock_v7 loaded: watertight=", dock.is_watertight,
          "bounds=", np.round(dock.bounds, 1).tolist())
    print("puck_cover loaded: watertight=", cover.is_watertight,
          "bounds=", np.round(cover.bounds, 1).tolist())

    body = build_puck_body()
    stub = build_cable_stub()
    print("\n[1] puck proxy: stadium body vol cm3=", round(float(body.volume) / 1000, 2),
          "(box proxy would be", round(PUCK_L * PUCK_W * PUCK_H / 1000, 2), ")",
          "bounds=", np.round(body.bounds, 1).tolist(), "watertight=", body.is_watertight)

    # ---- [2] insertion simulation -------------------------------------
    print("\n[2] insertion simulation (straight down, 2 mm steps)")
    print(" dz   body-only mm3   body+rigid-stub mm3")
    for dz in range(0, -32, -2):
        b = body.copy(); b.apply_translation((0, 0, dz))
        v_body, _ = inter(b, dock)
        bs = union([b, stub.copy()], engine="manifold") if dz == 0 else None
        if dz != 0:
            s = stub.copy(); s.apply_translation((0, 0, dz))
            bs = union([b, s], engine="manifold")
        v_bs, _ = inter(bs, dock)
        print(f" {dz:4d}  {v_body:12.3f}  {v_bs:14.3f}")

    # ---- [3] final-pose clearances ------------------------------------
    v_pd, _ = inter(body, dock)
    v_pc, _ = inter(body, cover)
    print("\n[3] final pose: puck x dock mm3 =", round(v_pd, 4))
    print("    final pose: puck x cover mm3 =", round(v_pc, 4),
          "(rails touch the puck bottom at Z", POCKET_FLOOR_Z, "- contact, no overlap)")
    print("    wall gaps: X total", round(POCKET_L - PUCK_L, 2), "mm ->",
          round((POCKET_L - PUCK_L) / 2, 2), "mm/side ; Y total",
          round(POCKET_W - PUCK_W, 2), "mm ->", round((POCKET_W - PUCK_W) / 2, 2), "mm/side")
    # numeric gap probe: expand body by g in XY and find first contact
    for g in (0.7, 0.79, 0.81, 1.0):
        big = box((PUCK_L + 2 * g, PUCK_W + 2 * g, PUCK_H),
                  (PUCK_CX, 0, POCKET_FLOOR_Z + PUCK_H / 2))
        v, _ = inter(big, dock)
        print(f"    body dilated {g} mm in XY: intersection with cavity walls mm3 = {round(v, 3)}")

    # straight stub alone vs dock (final pose)
    v_stub, m_stub = inter(stub, dock)
    print("\n[4a] straight stub (rigid, mid-height) x dock mm3 =", round(v_stub, 3))
    if m_stub is not None and v_stub > 0:
        print("     collision region bounds:", np.round(m_stub.bounds, 2).tolist())

    # ---- [4] routed cable ----------------------------------------------
    cable = build_routed_cable()
    v_cab, m_cab = inter(cable, dock)
    print("[4b] routed cable (bend into tunnel + back channel) x dock mm3 =", round(v_cab, 3))
    if m_cab is not None and v_cab > 0:
        print("     residual collision bounds:", np.round(m_cab.bounds, 2).tolist())
    for i, (a, b) in enumerate(zip(CABLE_PTS[:-1], CABLE_PTS[1:])):
        v, _ = inter(seg_cyl(a, b), dock)
        print(f"     seg {i} {a} -> {b}: {round(v, 3)} mm3")

    # ---- [5] aperture exposure -----------------------------------------
    # groove zone: stadium inset 4 mm -> stadium 33.0 x 19.0 @ (10,0), top face
    gz_L, gz_W = PUCK_L - 8, PUCK_W - 8
    print("\n[5] aperture exposure: groove zone", gz_L, "x", gz_W,
          "inside aperture", APERTURE_L, "x", APERTURE_W)
    print("    margin X per side:", round((APERTURE_L - gz_L) / 2, 2),
          "mm ; margin Y per side:", round((APERTURE_W - gz_W) / 2, 2), "mm")
    # puck top outline itself vs aperture: puck is 0.3 mm/side SMALLER
    print("    puck outline vs aperture: X", round((APERTURE_L - PUCK_L) / 2, 2),
          "mm/side, Y", round((APERTURE_W - PUCK_W) / 2, 2), "mm/side (aperture larger)")

    # ---- [6] fit-test slice --------------------------------------------
    slab = box((220, 220, 34), (5, -1, 17))       # Z 0..34, covers footprint
    fit = intersection([dock, slab], engine="manifold")
    out = os.path.join(MODELS, "puck_fit_test_v7.stl")
    trimesh.exchange.export.export_mesh(fit, out, file_type="stl_ascii")
    print("\n[6] puck_fit_test_v7.stl exported: vol cm3=", round(float(fit.volume) / 1000, 2),
          "bounds=", np.round(fit.bounds, 1).tolist(), "watertight=", fit.is_watertight)
    fit_r = load("puck_fit_test_v7.stl")
    print("    after ASCII reload: watertight=", fit_r.is_watertight, "is_volume=", fit_r.is_volume)
    v_pf, _ = inter(body, fit_r)
    v_cf, _ = inter(cover, fit_r)
    print("    puck seated in slice x slice mm3 =", round(v_pf, 4))
    print("    cover (fitted) x slice mm3 =", round(v_cf, 4))
    # same screw pilots + aperture ledge present in the slice?
    pilots = [(x, 0, 3.0) for x in (-14.5, 34.5)]
    print("    screw-pilot points inside slice (expect [False, False]):",
          fit_r.contains(np.array(pilots)).tolist())
    ring = [(x, y, 28.4) for x in np.linspace(-14, 34, 13) for y in (-16.5, 15.5)]
    ring += [(x, y, 28.4) for y in np.linspace(-12, 12, 9) for x in (-13.5, 33.5)]
    print("    seat ring solid at Z 28.4 in slice:",
          int(fit_r.contains(np.array(ring)).sum()), "/", len(ring))
    col = fit_r.contains(np.array([(10, 0, 27.5), (10, 0, 28.4)]))
    print("    aperture centre column open in slice (expect [False, False]):", col.tolist())
    print("\ndone")


if __name__ == "__main__":
    main()

