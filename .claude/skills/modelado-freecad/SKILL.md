---
name: modelado-freecad
description: Crea o actualiza el modelo paramétrico FreeCAD de un proyecto mediante script Python ejecutado sin interfaz.
---
1. Usa el agente `ingeniero-freecad`.
2. Genera `proyectos/<id>/modelo/<id>.py` a partir de `diseno.md`, usando `scripts/freecad/base.py`.
3. Ejecuta: `<ruta_freecadcmd> proyectos/<id>/modelo/<id>.py` → `<id>.FCStd`.
4. Ejecuta `scripts/freecad/validar.py` (sólidos válidos, interferencias, dimensiones vs diseño).
5. Exporta `salidas/<id>.step` y una imagen isométrica para que el usuario lo vea.
