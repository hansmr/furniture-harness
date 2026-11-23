# Harness de diseño de muebles (madera y PVC)

Este repositorio convierte una idea de mueble en un paquete de fabricación completo:
modelo FreeCAD, vista explotada, planos técnicos, lista de materiales y despiece,
guía de montaje e instalación.

## Regla cero: nada inventado
- Toda medida, material, herraje, proveedor o precio debe venir de `config/` o `catalogos/`
  o de lo que el usuario dijo en el brief. Si no está, se PREGUNTA. No se asume.
- Los valores marcados `PENDIENTE` en `config/proyecto.yaml` bloquean la fase que los usa.
- Las cotas de los planos se leen del modelo FreeCAD, nunca se escriben a mano.
- Cada salida termina con una sección "Supuestos y pendientes" (vacía si no hay).

## Flujo por fases
1. **Brief** (`/brief-de-diseno`) → `proyectos/<id>/brief.md` aprobado por el usuario.
2. **Modelo** (`/modelado-freecad`) → `proyectos/<id>/modelo/<id>.py` paramétrico + `.FCStd`.
3. **Revisión** (`/revision-diseno`) → validación estructural, de material y de fabricación.
4. **Salidas**: `/despiece-explotado`, `/plano-tecnico`, `/lista-materiales`, `/guia-montaje`.
No se pasa de fase sin aprobación explícita del usuario.

## Estructura
- `config/proyecto.yaml` – unidades, normas, herramientas, formatos (fuente de verdad).
- `catalogos/` – tableros, perfiles, tubos PVC, herrajes, uniones (solo datos verificados).
- `scripts/freecad/` – utilidades Python ejecutadas con `freecadcmd` (sin interfaz).
- `proyectos/<id>/` – un mueble por carpeta; copiar `proyectos/_plantilla/`.
- `.claude/agents/` – subagentes por especialidad. `.claude/skills/` – procedimientos reutilizables.

## Convenciones
- Idioma de salidas: español. Unidades: ver `config/proyecto.yaml`.
- Nombres de piezas: `<CÓDIGO>-<nn>` (p. ej. `LAT-01`), únicos por proyecto y usados igual
  en modelo, planos, lista de materiales y guía.
- El modelo es la única fuente de geometría; todo lo demás se genera desde él.
