"""Orthographic projection previews for the v6 pendant case (style of v5)."""
import importlib.util, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

spec = importlib.util.spec_from_file_location('b6', 'src/build_v6.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
import trimesh

IVORY = '#cbbfa5'
DARK = '#22262b'


def proj(ax, mesh, axes, color, alpha, maxf=9000):
    tris = mesh.triangles[:, :, axes]
    if len(tris) > maxf:
        idx = np.linspace(0, len(tris) - 1, maxf).astype(int); tris = tris[idx]
    patches = [MplPoly(t, closed=True) for t in tris]
    ax.add_collection(PatchCollection(patches, facecolor=color, edgecolor='none', alpha=alpha))


def panel(ax, meshes, axes, xlabel, ylabel, title, xinv=False):
    for m, c, a in meshes: proj(ax, m, axes, c, a)
    ax.set_aspect('equal'); ax.autoscale_view()
    if xinv: ax.invert_xaxis()
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title, fontsize=10); ax.grid(alpha=.2)


case = b.build_case_v6(); dummy = b.build_watch_dummy()
# worn orientation (crown up): (x,y,z) -> (-z, y, x), no translation
R = np.eye(4); R[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
case_w = case.copy(); case_w.apply_transform(R)
dummy_w = dummy.copy(); dummy_w.apply_transform(R)

fig, axs = plt.subplots(1, 3, figsize=(15, 5.6))
panel(axs[0], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [0, 2],
      'X (mm)', 'Z (mm)', 'Pendant v6, FRONT (worn: crown up, contacts down)')
panel(axs[1], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [1, 2],
      'Y (mm)  front (-)  back (+)', 'Z (mm)', 'Pendant v6, SIDE')
panel(axs[2], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [0, 2],
      'X (mm)', 'Z (mm)', 'Pendant v6, REAR (sensor window)', xinv=True)
plt.tight_layout(); plt.savefig('preview/pendant_v6.png', dpi=110); plt.close(); print('preview/pendant_v6.png')

dock = trimesh.load('models/dock_v5.stl')
both, case_d, dummy_d = b.build_docked()
fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
panel(axs[0], [(dock, IVORY, 0.45), (dummy_d, DARK, 0.9), (case_d, IVORY, 0.75)], [0, 2],
      'X (mm)  <- left eyelet', 'Z (mm)', 'v6 in dock v5, front: crown up, eyelets clear')
panel(axs[1], [(dock, IVORY, 0.45), (dummy_d, DARK, 0.9), (case_d, IVORY, 0.75)], [0, 1],
      'X (mm)', 'Y (mm)  back (+)', 'v6 in dock v5, top')
plt.tight_layout(); plt.savefig('preview/assembly_v6.png', dpi=110); plt.close(); print('preview/assembly_v6.png')
