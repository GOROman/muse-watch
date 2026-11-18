"""Orthographic projection preview for the v6.1 pendant case (style of v6)."""
import importlib.util, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection

spec = importlib.util.spec_from_file_location('b61', 'src/build_v6_1.py')
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
b6 = b.b6

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


case = b.build_case_v6_1(); dummy = b6.build_watch_dummy()
# worn orientation (crown up): (x,y,z) -> (-z, y, x), no translation
R = np.eye(4); R[:3, :3] = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
case_w = case.copy(); case_w.apply_transform(R)
dummy_w = dummy.copy(); dummy_w.apply_transform(R)

fig, axs = plt.subplots(1, 3, figsize=(15, 5.6))
panel(axs[0], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [0, 2],
      'X (mm)', 'Z (mm)', 'Pendant v6.1, FRONT (crown up, eyelet LEFT only)')
panel(axs[1], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [1, 2],
      'Y (mm)  front (-)  back (+)', 'Z (mm)', 'Pendant v6.1, SIDE')
panel(axs[2], [(dummy_w, DARK, 0.9), (case_w, IVORY, 0.55)], [0, 2],
      'X (mm)', 'Z (mm)', 'Pendant v6.1, REAR (sensor window)', xinv=True)
plt.tight_layout(); plt.savefig('preview/pendant_v6_1.png', dpi=110); plt.close()
print('preview/pendant_v6_1.png')
