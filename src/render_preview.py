import importlib.util, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly
from matplotlib.collections import PatchCollection
spec=importlib.util.spec_from_file_location('b','src/build_muse_watch.py'); b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)

def proj(ax, mesh, axes, color, alpha, maxf=6000):
    tris = mesh.triangles[:, :, axes]
    if len(tris) > maxf:
        idx = np.linspace(0, len(tris)-1, maxf).astype(int); tris = tris[idx]
    patches=[MplPoly(t, closed=True) for t in tris]
    ax.add_collection(PatchCollection(patches, facecolor=color, edgecolor='none', alpha=alpha))

def shot(meshes, axes, xlabel, ylabel, out, title, xlim=None, ylim=None):
    fig, ax = plt.subplots(figsize=(7,7))
    for m,c,a in meshes: proj(ax,m,axes,c,a)
    ax.set_aspect('equal'); ax.autoscale_view()
    if xlim: ax.set_xlim(*xlim)
    if ylim: ax.set_ylim(*ylim)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); ax.set_title(title); ax.grid(alpha=.2)
    plt.tight_layout(); plt.savefig(out, dpi=110); plt.close(); print(out)

dock=b.build_dock(); dummy=b.build_dummy(); shell=b.build_pendant_shell_v4()
# Front view = projection on XZ (looking from -Y, display side)
shot([(dock,'#3a7ca5',0.55),(dummy,'#111111',0.85)], [0,2], 'X (mm)  <- cord / tower        crown side ->', 'Z (mm)', 'preview/assembly_front.png', 'Docked, front view: charging edge down on the puck, crown up, tower+cord left')
# Top view = XY
shot([(dock,'#3a7ca5',0.55),(dummy,'#111111',0.85)], [0,1], 'X (mm)', 'Y (mm)  back (+)', 'preview/assembly_top.png', 'Docked, top view')
# Shell front view = XZ in pendant frame... shell axes: X right, Z up -> use [0,2] with Y depth ignored
shot([(shell,'#333333',0.8)], [0,2], 'X (mm)  charging side open at left', 'Z (mm)', 'preview/pendant_shell_v4.png', 'Pendant shell v4, front: left side cut open for docking')
shot([(dock,'#3a7ca5',0.8)], [0,2], 'X (mm)', 'Z (mm)', 'preview/dock.png', 'Dock, front view: saddle + puck pocket at bottom centre, wall on the right, cord bay open on the left')
