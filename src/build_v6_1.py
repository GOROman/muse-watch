#!/usr/bin/env python3
"""
Muse Watch pendant case v6.1 — v6 bumper with the user corrections of
2026-11-18 17:09 (design/DESIGN_V6_PENDANT.md, CORRECTIONS section):

  * STRAP EYELET LEFT ONLY. In the worn/front orientation (crown up,
    glass facing the viewer) the eyelet sits on the viewer's LEFT.
    Worn frame: (x,y,z)_worn = (-z, y, x) of the watch frame, front view
    screen-right = +X_worn = -Z_watch. So the viewer's-left eyelet is the
    watch-frame eyelet at Z = +EYELET_ZC, and the removed one is the
    watch-frame eyelet at Z = -EYELET_ZC (it sat over the v7 dock's right
    fin). On the removed side the bumper is the plain revolved profile:
    no lug, no hole, nothing beyond OUT_R.
  * CHARGING AREA OPEN — unchanged from v6: chord cut at CHORD_X leaves
    the whole -X edge band (contact pads + speaker) free of material;
    re-verified below by a probe box over the contact patch.

Everything else (bumper profile, crown notch, button cutout, dummy,
docked transform, single-material PETG recommendation) is v6, reused by
importing src/build_v6.py so the geometry cannot drift.

Parts exported (ASCII STL, models/):
  pendant_shell_v6_1.stl    — the v6.1 case, watch frame
  pendant_v6_1_docked.stl   — case + watch dummy, v5 dock pose
"""
import importlib.util
import os
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(ROOT, "models")

_spec = importlib.util.spec_from_file_location("build_v6", os.path.join(HERE, "build_v6.py"))
b6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b6)

VERSION = "6.1"
KEPT_SIGN = +1   # watch-frame +Z eyelet == viewer's LEFT when worn (see docstring)


# ---------------------------------------------------------------- case v6.1
def build_eyelet_lug():
    """The single (kept) eyelet lug with its oval hole, watch frame."""
    lug = b6.rounded_plate(b6.EYELET_SX, b6.EYELET_SZ, b6.EYELET_T, r=4.0,
                           z0=-b6.EYELET_T / 2)
    lug.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    lug.apply_translation((0, 0, KEPT_SIGN * b6.EYELET_ZC))
    holes = [b6.cyl(b6.HOLE_R * 2, b6.EYELET_T + 4,
                    (dx, 0, KEPT_SIGN * b6.EYELET_ZC), axis="y")
             for dx in (-b6.HOLE_DX, b6.HOLE_DX)]
    return b6.difference([lug] + holes, engine="manifold")


def build_case_v6_1():
    case = b6.lathe(b6.PROFILE)
    lug = build_eyelet_lug()
    case = b6.union([case, lug], engine="manifold")

    cuts = []
    # Crown notch: +X sector, leaves guard humps at |z| > 6.8 (as v6)
    cuts.append(b6.box((14, b6.CROWN_NOTCH["y"][1] - b6.CROWN_NOTCH["y"][0],
                        b6.CROWN_NOTCH["z"] * 2),
                       (b6.CROWN_NOTCH["x0"] + 7, sum(b6.CROWN_NOTCH["y"]) / 2, 0)))
    # Side-button cutout (as v6)
    a = np.radians(b6.BUTTON_ANG)
    d = np.array([np.cos(a), 0, np.sin(a)])
    bc = trimesh.creation.cylinder(radius=b6.BUTTON_CUT_R, height=16, sections=48)
    bc.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], d))
    bc.apply_translation(tuple(d * 24.0 + [0, b6.CROWN_Y, 0]))
    cuts.append(bc)
    # Contacts opening: chord cut at -X (full slab, as v6) — the -Z eyelet
    # holes of v6 are GONE together with that lug; nothing else changes.
    cuts.append(b6.box((14.2, 20, 44), (b6.CHORD_X - 7.1, 0, 0)))
    case = b6.difference([case] + cuts, engine="manifold")
    return case


def build_docked_v6_1():
    case = build_case_v6_1()
    dummy = b6.build_watch_dummy()
    case_d = case.copy(); case_d.apply_transform(b6.DOCK_T)
    dummy_d = dummy.copy(); dummy_d.apply_transform(b6.DOCK_T)
    both = trimesh.util.concatenate([case_d, dummy_d])
    return both, case_d, dummy_d


if __name__ == "__main__":
    os.makedirs(MODELS, exist_ok=True)
    case = build_case_v6_1()
    dummy = b6.build_watch_dummy()

    print(f"=== pendant case v{VERSION} ===")
    print("--- case vs watch (watch frame) ---")
    print("case watertight=", case.is_watertight,
          "vol_cm3=", round(float(case.volume) / 1000, 2))
    print("case x dummy intersection cm3:", round(b6.inter_vol(case, dummy) / 1000, 5))
    print("case bounds:", np.round(case.bounds, 2).tolist())

    print("--- removed-eyelet side (watch -Z) ---")
    v = case.vertices
    neg = v[v[:, 2] < 0]
    r_xz = np.sqrt(neg[:, 0] ** 2 + neg[:, 2] ** 2)
    print("max radial extent (XZ) on -Z half:", round(float(r_xz.max()), 3),
          "mm  (bumper OUT_R =", b6.OUT_R, ")")
    print("case min Z:", round(float(case.bounds[0][2]), 2),
          "(bumper only, -OUT_R) | max Z:", round(float(case.bounds[1][2]), 2),
          "(kept lug tip)")

    print("--- kept eyelet hole openness ---")
    axis_pts = np.array([[dx, y, KEPT_SIGN * b6.EYELET_ZC]
                         for dx in (-b6.HOLE_DX, b6.HOLE_DX)
                         for y in np.linspace(-6, 6, 13)])
    inside = case.contains(axis_pts)
    print("hole-axis sample points inside case:", int(inside.sum()), "/", len(axis_pts),
          "(0 = hole fully open)")

    print("--- charging-contacts opening ---")
    print("case min X:", round(float(case.bounds[0][0]), 2),
          "(chord plane CHORD_X =", b6.CHORD_X, ") | dummy min X:",
          round(float(dummy.bounds[0][0]), 2), "(watch edge protrudes past chord)")
    probe = b6.box((4.19, 14.44, 28), (-21.9, 0, 0))  # x -24..-19.81, full thickness band
    print("contact-patch probe x case intersection mm3:",
          round(b6.inter_vol(probe, case), 3))

    both, case_d, dummy_d = build_docked_v6_1()
    b6.export(case, "pendant_shell_v6_1.stl")
    b6.export(both, "pendant_v6_1_docked.stl")

    print("--- reload check ---")
    for name in ("pendant_shell_v6_1.stl", "pendant_v6_1_docked.stl"):
        m = trimesh.load(os.path.join(MODELS, name), process=False)
        m.merge_vertices()
        print(name, "reloaded watertight=", m.is_watertight, "is_volume=", m.is_volume)

    print("--- dock fit (docked pose) ---")
    for dock_name in ("dock_v7.stl", "dock_v5.stl"):
        dock = trimesh.load(os.path.join(MODELS, dock_name))
        print(dock_name,
              "| assembly x dock cm3:", round(b6.inter_vol(both, dock) / 1000, 5),
              "| case x dock cm3:", round(b6.inter_vol(case_d, dock) / 1000, 5),
              "| dummy x dock cm3:", round(b6.inter_vol(dummy_d, dock) / 1000, 5))
        pts = case_d.sample(6000)
        _, dist, _ = trimesh.proximity.closest_point(dock, pts)
        print("   case->dock min distance mm:", round(float(np.min(dist)), 2))

    print("--- left eyelet vs dock v7 left fin slot ---")
    # build_v7.py: left fin X band -20.5..-17.5; slot cut box 7x15x13 at
    # centre (-19, 0, 46) -> X -22.5..-15.5, Y +-7.5, Z 39.5..52.5.
    dock7 = trimesh.load(os.path.join(MODELS, "dock_v7.stl"))
    lug_d = build_eyelet_lug(); lug_d.apply_transform(b6.DOCK_T)
    print("lug(docked) x dock_v7 intersection mm3:", round(b6.inter_vol(lug_d, dock7), 3))
    print("lug docked bounds:", np.round(lug_d.bounds, 2).tolist(),
          " (slot: X -22.5..-15.5, Y -7.5..7.5, Z 39.5..52.5; fin band X -20.5..-17.5)")
    pts = lug_d.sample(3000)
    _, dist, _ = trimesh.proximity.closest_point(dock7, pts)
    print("lug->dock_v7 min distance mm:", round(float(np.min(dist)), 2))
    print("done")
