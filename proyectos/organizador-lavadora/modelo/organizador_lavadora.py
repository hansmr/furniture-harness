"""Modelo FreeCAD del organizador de lavadora.
Uso (Windows):  "C:\\Program Files\\FreeCAD 1.1\\bin\\freecadcmd.exe" organizador_lavadora.py
Genera organizador-lavadora.FCStd y ../salidas/organizador-lavadora.step junto a este archivo.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import FreeCAD as App  # noqa: E402
import Part            # noqa: E402
import geometria as g  # noqa: E402

V = App.Vector


def tubo(a, b, de):
    a, b = V(*a), V(*b)
    return Part.makeCylinder(de / 2, (b - a).Length, a, (b - a).normalize())


def cuerpo_accesorio(centro, de, largo, ramas):
    """Aproximación visual: cilindro por cada dirección de rama desde el centro."""
    c = V(*centro)
    sol = None
    for d in ramas:
        cil = Part.makeCylinder(de / 2, largo / 2, c, V(*d))
        sol = cil if sol is None else sol.fuse(cil)
    return sol.removeSplitter()


def tablero(origen, dims, perforaciones, de_perf, muesca=None):
    caja = Part.makeBox(*dims, V(*origen))
    if muesca:
        mx, mf, mb = muesca
        x0, y0, z0 = origen
        for (ex, ey, my) in ((x0, y0, mf), (x0 + dims[0] - mx, y0, mf),
                             (x0, y0 + dims[1] - mb, mb), (x0 + dims[0] - mx, y0 + dims[1] - mb, mb)):
            caja = caja.cut(Part.makeBox(mx, my, dims[2] + 2, V(ex, ey, z0 - 1)))
    for (x, y) in perforaciones:
        caja = caja.cut(Part.makeCylinder(de_perf / 2, dims[2] + 2, V(x, y, origen[2] - 1)))
    return caja


def construir():
    doc = App.newDocument("organizador_lavadora")
    perf = g.TUBO_DE + 2  # PROPUESTA: holgura 1 mm por lado
    for p in g.piezas():
        if p["tipo"] == "tubo":
            shp = tubo(p["a"], p["b"], p["de"])
        elif p["tipo"] in ("tee", "codo"):
            if p["tipo"] == "codo":
                brazo = min(g.CODO["extremos"]) - g.CODO["de"] / 2
                shp = cuerpo_accesorio(p["centro"], g.CODO["de"], 2 * brazo, p["ramas"])
            else:
                shp = cuerpo_accesorio(p["centro"], g.TEE["de"], g.TEE["largo"], p["ramas"])
        elif p["tipo"] == "diagonal":
            v = g.vertices_diagonal(p)
            cara = Part.Face(Part.makePolygon([V(*q) for q in v[:4]] + [V(*v[0])]))
            shp = cara.extrude(V(p["sx"] * p["espesor"], 0, 0))
        else:
            shp = tablero(p["origen"], p["dims"], p["perforaciones"], perf, p.get("muesca"))  # tablero o listón
        obj = doc.addObject("Part::Feature", p["codigo"].replace("-", "_"))
        obj.Label = p["codigo"]
        obj.Shape = shp
        obj.addProperty("App::PropertyString", "Material", "Mueble")
        obj.Material = {"tablero": "Triplex 15 mm (TRX-15)", "diagonal": "Triplex 15 mm (TRX-15)", "liston": "PENDIENTE (listón 18 mm)"}.get(p["tipo"], "PVC presión 1\" RDE 13.5")
    doc.recompute()
    return doc


if True:  # freecadcmd ejecuta el script directamente
    doc = construir()
    salidas = os.path.join(AQUI, "..", "salidas")
    os.makedirs(salidas, exist_ok=True)
    doc.saveAs(os.path.join(AQUI, "organizador-lavadora.FCStd"))
    import Import
    Import.export([o for o in doc.Objects if hasattr(o, "Shape")], os.path.join(salidas, "organizador-lavadora.step"))
    for ok, t in g.verificaciones():
        print("OK   " if ok else "FALTA", t)
    # Interferencias entre piezas (los accesorios son cilindros aproximados; los tubos entran en ellos a propósito)
    objs = [o for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Volume > 0]
    choques = 0
    for i, a in enumerate(objs):
        for b in objs[i + 1:]:
            tipos = {a.Label[:3], b.Label[:3]}
            if tipos <= {"TUB", "TEE", "COD"}:
                continue  # unión tubo-accesorio prevista
            if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):
                continue
            v = a.Shape.common(b.Shape).Volume
            if v > 1.0:
                choques += 1
                print(f"CHOQUE {a.Label} x {b.Label}: {v:.0f} mm3")
    print(f"Interferencias de madera: {choques}")
    for h in g.herrajes():
        print(f"  herraje {h['codigo']}: {h['descripcion']} x {h['cantidad']} ({h['modelo']})")
    for c, L in g.longitudes_corte():
        print(f"  corte {c}: {L} mm")
    # Vistas PNG solo si hay interfaz gráfica (freecadcmd no la tiene)
    print("Modelo guardado.")
