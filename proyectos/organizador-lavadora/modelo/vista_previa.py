"""Render conceptual rápido (sin FreeCAD) desde geometria.py. No sustituye al modelo FreeCAD."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import geometria as g

def caja(ax, o, d, color, alpha):
    x, y, z = o; dx, dy, dz = d
    v = [(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z),(x,y,z+dz),(x+dx,y,z+dz),(x+dx,y+dy,z+dz),(x,y+dy,z+dz)]
    f = [[0,1,2,3],[4,5,6,7],[0,1,5,4],[2,3,7,6],[1,2,6,5],[0,3,7,4]]
    ax.add_collection3d(Poly3DCollection([[v[i] for i in c] for c in f], facecolor=color, edgecolor="#555", linewidths=0.4, alpha=alpha))

def dibujar(ax, elev, azim, titulo):
    L = g.LAVADORA
    caja(ax, (-L["ancho"]/2, -L["fondo"]/2, 0), (L["ancho"], L["fondo"], L["alto"]), "#cfd8dc", 0.35)
    ax.plot([-L["ancho"]/2, L["ancho"]/2], [g.CY-40]*2, [L["alto_tapa_abierta"]]*2, "r--", lw=1)
    for p in g.piezas():
        if p["tipo"] == "tubo":
            (x0,y0,z0),(x1,y1,z1) = p["a"], p["b"]
            ax.plot([x0,x1],[y0,y1],[z0,z1], color="#455a64", lw=4, solid_capstyle="round")
            ax.plot([x0,x1],[y0,y1],[z0,z1], color="#90a4ae", lw=1)
        elif p["tipo"] in ("tee","codo"):
            ax.scatter(*p["centro"], s=40, color="#78909c")
        else:
            caja(ax, p["origen"], p["dims"], "#d7a86e", 0.6)
    ax.set_xlim(-450,450); ax.set_ylim(-450,450); ax.set_zlim(0,2080)
    ax.set_box_aspect((900,900,2080)); ax.view_init(elev, azim); ax.set_title(titulo, fontsize=10)
    ax.set_xlabel("X mm"); ax.set_ylabel("Y mm"); ax.set_zlabel("Z mm")

fig = plt.figure(figsize=(12, 10), dpi=130)
dibujar(fig.add_subplot(1,2,1, projection="3d"), 18, -60, "Isométrica (lavadora en gris, línea roja = tapa abierta 1240 mm)")
dibujar(fig.add_subplot(1,2,2, projection="3d"), 0, -90, "Frontal")
fig.suptitle("Organizador de lavadora — PROPUESTA conceptual (tubo PVC 1\", triplex 15 mm)", fontsize=12)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "salidas", "vista-previa-concepto.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, bbox_inches="tight"); print(out)
