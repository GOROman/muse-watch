"""Orthographic projection previews for the v5 dock (style of render_preview.py)."""
import importlib.util, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

spec = importlib.util.spec_from_file_location('b5', 'src/build_v5.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

IVORY = '#cbbfa5'   # dock body (print in ivory PLA)
ORANGE = '#e86a17'  # accent disc
DARK = '#22262b'    # pendant shell


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


dock = b.build_dock_v5(); disc = b.build_accent_disc(); dummy = b.build_dummy_v5()

# Dock alone: front (XZ) + side (YZ) — side shows the cradle profile:
# front lip, seat at Z 28.5, back wall + gusset behind.
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
panel(axs[0], [(dock, IVORY, 0.9), (disc, ORANGE, 1.0)], [0, 2],
      'X (mm)  <- cord bay (open)', 'Z (mm)', 'Dock v5, front')
panel(axs[1], [(dock, IVORY, 0.9)], [1, 2],
      'Y (mm)  front (-)  back (+)', 'Z (mm)', 'Dock v5, side: lip / seat 28.5 / wall')
plt.tight_layout(); plt.savefig('preview/dock_v5.png', dpi=110); plt.close(); print('preview/dock_v5.png')

# Assembly: front (XZ) + top (XY). Front: shell docked, crown up, tower left.
# Top: seat aperture zone, open cord bay at the left, disc on the right cheek.
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
panel(axs[0], [(dock, IVORY, 0.5), (dummy, DARK, 0.9), (disc, ORANGE, 1.0)], [0, 2],
      'X (mm)  <- tower / cord', 'Z (mm)', 'Docked v5, front: crown up')
panel(axs[1], [(dock, IVORY, 0.5), (dummy, DARK, 0.9), (disc, ORANGE, 1.0)], [0, 1],
      'X (mm)', 'Y (mm)  back (+)', 'Docked v5, top')
plt.tight_layout(); plt.savefig('preview/assembly_v5.png', dpi=110); plt.close(); print('preview/assembly_v5.png')
