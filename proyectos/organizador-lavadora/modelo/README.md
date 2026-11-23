# Modelo del organizador de lavadora

- `geometria.py`: parámetros y piezas (fuente única de geometría). `python geometria.py` corre las verificaciones.
- `organizador_lavadora.py`: construye el modelo en FreeCAD y exporta STEP.
  Windows: `"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe" organizador_lavadora.py`
- `vista_previa.py`: render conceptual rápido con matplotlib (no reemplaza al modelo FreeCAD).

Los accesorios (tees, codos) se modelan como cilindros aproximados con las medidas del usuario; no son geometría exacta del fabricante.
