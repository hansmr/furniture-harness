"""Uso: freecadcmd extraer_bom.py <archivo.FCStd> <salida.csv>
Dimensiones = caja envolvente ordenada (largo >= ancho >= grosor)."""
import csv
import sys
import FreeCAD as App

ruta_fcstd, ruta_csv = sys.argv[-2], sys.argv[-1]
doc = App.openDocument(ruta_fcstd)
with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codigo", "material", "largo", "ancho", "grosor", "volumen"])
    for o in doc.Objects:
        if not hasattr(o, "Shape") or o.Shape.Volume <= 0:
            continue
        bb = o.Shape.BoundBox
        l, a, g = sorted([bb.XLength, bb.YLength, bb.ZLength], reverse=True)
        w.writerow([o.Label, getattr(o, "Material", ""), round(l, 1), round(a, 1), round(g, 1), round(o.Shape.Volume, 1)])
print("BOM escrita en", ruta_csv)
