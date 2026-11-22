---
name: lista-materiales
description: Produce lista de materiales, herrajes, despiece de corte y costo estimado desde el modelo FreeCAD.
---
1. Ejecuta `scripts/freecad/extraer_bom.py <FCStd>` → CSV de piezas.
2. Agrupa con `calculista-materiales`; aplica kerf y optimización de tablero/tubo.
3. Salidas: `salidas/bom.csv`, `salidas/bom.xlsx`, `salidas/despiece.md`.
