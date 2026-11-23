"""Uso: freecadcmd validar.py <archivo.FCStd>  -> sólidos válidos e interferencias."""
import sys
import FreeCAD as App

doc = App.openDocument(sys.argv[-1])
piezas = [o for o in doc.Objects if hasattr(o, "Shape") and o.Shape.Volume > 0]
errores = 0
for p in piezas:
    if not p.Shape.isValid():
        print(f"ERROR sólido inválido: {p.Label}"); errores += 1
for i, a in enumerate(piezas):
    for b in piezas[i + 1:]:
        v = a.Shape.common(b.Shape).Volume
        if v > 1e-3:
            print(f"ERROR interferencia {a.Label} ∩ {b.Label}: {v:.1f} mm³"); errores += 1
print(f"{len(piezas)} piezas, {errores} errores")
sys.exit(1 if errores else 0)
