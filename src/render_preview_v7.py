"""Orthographic projection previews for the v7 dock (style of render_preview_v5.py)."""
import importlib.util, numpy as np, trimesh, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

spec = importlib.util.spec_from_file_location('b7', 'src/build_v7.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

IVORY = '#cbbfa5'   # dock body (print in ivory PLA)
ORANGE = '#e86a17'  # accent badge
DARK = '#22262b'    # pendant (v6 case + watch dummy)


def proj(ax, mesh, axes, color, alpha, maxf=9000):
    tris = mesh.triangles[:, :, axes]
    if len(tris) > maxf:
        idx = np.linspace(0, len(tris) - 1, maxf).astype(int); tris = tris[idx]
    patches = [MplPoly(t, closed=True) for t in tris]
    ax.add_collection(PatchCollection(patches, facecolor=color, edgecolor='none', alpha=alpha))


def panel(ax, meshes, axes, xlabel, ylabel, title):
    for m, c, a in meshes: proj(ax, m, axes, c, a)
    ax.set_aspect('equal'); ax.autoscale_view()
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10); ax.grid(alpha=.2)


dock = b.build_dock_v7(); badge = b.build_accent_badge()
pendant = trimesh.load('models/pendant_v6_docked.stl')

# Dock alone: front (XZ) + side (YZ) — side shows the trapezoid profile:
# sloped front wedge, seat at Z 28.5, tall back wall with crown notch.
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
panel(axs[0], [(dock, IVORY, 0.9), (badge, ORANGE, 1.0)], [0, 2],
      'X (mm)', 'Z (mm)', 'Dock v7, front: badge lower right, fins + wall behind')
panel(axs[1], [(dock, IVORY, 0.9)], [1, 2],
      'Y (mm)  front (-)  back (+)', 'Z (mm)', 'Dock v7, side: wedge / seat 28.5 / wall + notch')
plt.tight_layout(); plt.savefig('preview/dock_v7.png', dpi=110); plt.close(); print('preview/dock_v7.png')

# Assembly: front (XZ) + top (XY). Front: v6 pendant docked, crown up,
# eyelets through the fin slots; top: seat aperture + fins flanking the case.
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
panel(axs[0], [(dock, IVORY, 0.5), (pendant, DARK, 0.9), (badge, ORANGE, 1.0)], [0, 2],
      'X (mm)', 'Z (mm)', 'Docked v7, front: crown up, eyelets in fin slots')
panel(axs[1], [(dock, IVORY, 0.5), (pendant, DARK, 0.9)], [0, 1],
      'X (mm)', 'Y (mm)  back (+)', 'Docked v7, top')
plt.tight_layout(); plt.savefig('preview/assembly_v7.png', dpi=110); plt.close(); print('preview/assembly_v7.png')
