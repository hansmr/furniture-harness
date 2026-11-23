"""Render conceptual (sin FreeCAD) desde geometria.py: vista general, frontal, lateral y detalle de unión.
No sustituye al modelo FreeCAD. Accesorios aproximados como cilindros."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import geometria as g

C_TUBO, C_ACC, C_MAD, C_LIS, C_LAV = "#eceff1", "#90a4ae", "#d7a86e", "#a1887f", "#cfd8dc"

def caja(ax, o, d, color, alpha, ec="#5d4037"):
    x, y, z = o; dx, dy, dz = d
    v = np.array([(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z),(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)])
    f = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    ax.add_collection3d(Poly3DCollection([v[c] for c in f], facecolor=color, edgecolor=ec, linewidths=0.5, alpha=alpha))

def cilindro(ax, a, b, r, color, n=18):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a; L = np.linalg.norm(d); d /= L
    t = np.array([1,0,0]) if abs(d[0]) < 0.9 else np.array([0,1,0])
    u = np.cross(d, t); u /= np.linalg.norm(u); w = np.cross(d, u)
    th = np.linspace(0, 2*np.pi, n); s = np.array([0, L])
    TH, S = np.meshgrid(th, s)
    P = a[:,None,None] + d[:,None,None]*S + r*(u[:,None,None]*np.cos(TH) + w[:,None,None]*np.sin(TH))
    ax.plot_surface(P[0], P[1], P[2], color=color, linewidth=0, shade=True, antialiased=True)

def prisma(ax, poly, z0, h, color, alpha, ec="#5d4037"):
    n = len(poly)
    bot = [(x, y, z0) for x, y in poly]; top = [(x, y, z0 + h) for x, y in poly]
    caras = [bot, top] + [[bot[i], bot[(i+1)%n], top[(i+1)%n], top[i]] for i in range(n)]
    ax.add_collection3d(Poly3DCollection(caras, facecolor=color, edgecolor=ec, linewidths=0.5, alpha=alpha))

def poly_muescas(o, d, m):
    x0, y0 = o[0], o[1]; x1, y1 = x0 + d[0], y0 + d[1]; mx, mf, mb = m
    return [(x0+mx, y0), (x1-mx, y0), (x1-mx, y0+mf), (x1, y0+mf), (x1, y1-mb), (x1-mx, y1-mb), (x1-mx, y1),
            (x0+mx, y1), (x0+mx, y1-mb), (x0, y1-mb), (x0, y0+mf), (x0+mx, y0+mf)]

def recortar_seg(a, b, lim):
    a, b = np.array(a, float), np.array(b, float); t0, t1 = 0.0, 1.0
    for i, (lo, hi) in enumerate(lim):
        d = b[i] - a[i]
        if abs(d) < 1e-9:
            if not lo <= a[i] <= hi: return None
            continue
        ta, tb = (lo - a[i]) / d, (hi - a[i]) / d
        t0, t1 = max(t0, min(ta, tb)), min(t1, max(ta, tb))
    return None if t0 >= t1 else (a + (b-a)*t0, a + (b-a)*t1)

def recortar_caja(o, d, lim):
    lo = [max(o[i], lim[i][0]) for i in range(3)]; hi = [min(o[i]+d[i], lim[i][1]) for i in range(3)]
    return None if any(h <= l for l, h in zip(lo, hi)) else (lo, [h-l for l, h in zip(lo, hi)])

def dentro(c, lim): return all(lo <= v <= hi for v, (lo, hi) in zip(c, lim))

def dibujar(ax, lim, elev, azim, titulo, lavadora=True, etiquetas=False):
    if etiquetas:
        ax.set_xlabel("X mm", fontsize=7); ax.set_ylabel("Y mm", fontsize=7); ax.set_zlabel("Z mm", fontsize=7)
    if lavadora:
        L = g.LAVADORA
        caja(ax, (-L["ancho"]/2, -L["fondo"]/2, 0), (L["ancho"], L["fondo"], L["alto"]), C_LAV, 0.25, "#90a4ae")
        ax.plot([-L["ancho"]/2, L["ancho"]/2], [0, 0], [L["alto_tapa_abierta"]]*2, "r--", lw=1)
    for p in g.piezas():
        if p["tipo"] == "tubo":
            seg = recortar_seg(p["a"], p["b"], lim)
            if seg: cilindro(ax, seg[0], seg[1], g.TUBO_DE/2, C_TUBO)
        elif p["tipo"] in ("tee", "codo"):
            c = np.array(p["centro"], float)
            if not dentro(c, lim): continue
            for d in p["ramas"]:
                cilindro(ax, c, c + np.array(d)*g.TEE["largo"]/2, g.TEE["de"]/2, C_ACC)
            if etiquetas:
                ax.text(*(c + np.array([45, -60, 0])), p["codigo"], fontsize=7)
        elif p.get("muesca") and not etiquetas:
            prisma(ax, poly_muescas(p["origen"], p["dims"], p["muesca"]), p["origen"][2], p["dims"][2], C_MAD, 0.55)
        elif p.get("muesca"):
            # detalle: recorta el polígono con muescas al cuadro de la vista
            (xa, xb), (ya, yb), _ = lim
            pts = [(min(max(x, xa), xb), min(max(y, ya), yb)) for x, y in poly_muescas(p["origen"], p["dims"], p["muesca"])]
            prisma(ax, pts, p["origen"][2], p["dims"][2], C_MAD, 0.55)
            ax.text(xa + (xb-xa)*0.3, ya + (yb-ya)*0.5, p["origen"][2] + 25, p["codigo"], fontsize=8)
        else:
            r = recortar_caja(p["origen"], p["dims"], lim)
            if not r: continue
            o, d = r
            col = C_LIS if p["tipo"] == "liston" else C_MAD
            caja(ax, o, d, col, 0.95 if p["tipo"] == "liston" else (0.5 if p["codigo"].startswith("EST") else 0.35))
            if etiquetas:
                ax.text(o[0]+d[0]*0.3, o[1]+d[1]*0.5, o[2]+d[2]+10, p["codigo"], fontsize=8)
    (x0,x1),(y0,y1),(z0,z1) = lim
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_zlim(z0,z1)
    ax.set_box_aspect((x1-x0, y1-y0, z1-z0)); ax.view_init(elev, azim)
    ax.set_title(titulo, fontsize=10); ax.tick_params(labelsize=6)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "salidas")
os.makedirs(out_dir, exist_ok=True)
GEN = ((-450,450),(-450,450),(0,2080))

fig = plt.figure(figsize=(16, 11), dpi=140)
dibujar(fig.add_subplot(1,3,1, projection="3d"), GEN, 20, -55, "Isométrica\n(gris = lavadora; rojo = tapa abierta 1240 mm)")
dibujar(fig.add_subplot(1,3,2, projection="3d"), GEN, 0, -90, "Frontal")
dibujar(fig.add_subplot(1,3,3, projection="3d"), GEN, 0, 0, "Lateral")
fig.suptitle('Organizador de lavadora — PROPUESTA (PVC 1" RDE 13.5, triplex 15 mm)', fontsize=13)
fig.savefig(os.path.join(out_dir, "vista-previa-concepto.png"), bbox_inches="tight")

fig = plt.figure(figsize=(14, 7), dpi=150)
cx, cy, z1 = g.CX, g.CY, g.Z_EST1
dibujar(fig.add_subplot(1,2,1, projection="3d"), ((cx-200, cx+80),(-cy-80, -cy+200),(z1-120, z1+160)), 22, -50,
        "Detalle esquina delantera, estante 1", lavadora=False, etiquetas=True)
dibujar(fig.add_subplot(1,2,2, projection="3d"), ((cx-200, cx+80),(-cy-80, -cy+200),(g.Z_EST2-120, g.Z_EST2+160)), 22, -50,
        "Detalle esquina delantera, estante 2 (remate)", lavadora=False, etiquetas=True)
fig.suptitle("Uniones: estante 1 con muescas que abrazan el paral; estante 2 entero sobre los codos. Ambos apoyan en listones y se fijan con abrazaderas", fontsize=11)
fig.savefig(os.path.join(out_dir, "vista-detalle-uniones.png"), bbox_inches="tight")
print("ok")
