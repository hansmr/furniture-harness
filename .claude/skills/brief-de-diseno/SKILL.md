---
name: brief-de-diseno
description: Inicia un mueble nuevo: crea la carpeta del proyecto y obtiene un brief completo preguntando al usuario todo lo que falte.
---
1. Copia `proyectos/_plantilla/` a `proyectos/<id>/` (id en kebab-case).
2. Revisa `config/proyecto.yaml`; si hay `PENDIENTE` que afecte a este mueble, pregúntalo primero.
3. Rellena `brief.md` solo con respuestas del usuario. Pregunta en bloques cortos lo que falte.
4. Muestra el brief y pide aprobación explícita antes de pasar a diseño.
