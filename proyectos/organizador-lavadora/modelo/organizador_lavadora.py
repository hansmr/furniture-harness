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


def tablero(origen, dims, perforaciones, de_perf):
    caja = Part.makeBox(*dims, V(*origen))
    for (x, y) in perforaciones:
        caja = caja.cut(Part.makeCylinder(de_perf / 2, dims[2] + 2, V(x, y, origen[2] - 1)))
    return caja


def construir():
    doc = App.newDocument("organizador_lavadora")
    perf = g.TUBO_DE + 2  # PROPUESTA: holgura 1 mm por lado
    for p in g.piezas():
        if p["tipo"] == "tubo":
            shp = tubo(p["a"], p["b"], p["de"])
        elif p["tipo"] == "tee":
            x, y, z = p["centro"]
            sx = -1 if x > 0 else 1  # rama hacia el interior en X
            shp = cuerpo_accesorio(p["centro"], g.TEE["de"], g.TEE["largo"], [(0, 0, 1), (0, 0, -1), (sx, 0, 0)])
        elif p["tipo"] == "codo":
            x, y, z = p["centro"]
            vert = (0, 0, 1) if z < 1000 else (0, 0, -1)
            horiz = (0, -1 if y > 0 else 1, 0) if z < 1000 else (-1 if x > 0 else 1, 0, 0)
            shp = cuerpo_accesorio(p["centro"], g.TEE["de"], g.TEE["largo"], [vert, horiz])
        else:
            shp = tablero(p["origen"], p["dims"], p["perforaciones"], perf)
        obj = doc.addObject("Part::Feature", p["codigo"].replace("-", "_"))
        obj.Label = p["codigo"]
        obj.Shape = shp
        obj.addProperty("App::PropertyString", "Material", "Mueble")
        obj.Material = "Triplex 15 mm (TRX-15)" if p["tipo"] == "tablero" else "PVC presión 1\" RDE 13.5"
    doc.recompute()
    return doc


if __name__ == "__main__" or True:
    doc = construir()
    salidas = os.path.join(AQUI, "..", "salidas")
    os.makedirs(salidas, exist_ok=True)
    doc.saveAs(os.path.join(AQUI, "organizador-lavadora.FCStd"))
    import Import
    Import.export([o for o in doc.Objects if hasattr(o, "Shape")], os.path.join(salidas, "organizador-lavadora.step"))
    for ok, t in g.verificaciones():
        print("OK   " if ok else "FALTA", t)
    print("Modelo guardado.")
