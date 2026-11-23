"""Genera el paquete de fabricación del organizador desde geometria.py (fuente única de medidas).

Salidas en ../salidas/:
  bom.csv, bom.xlsx, despiece.md       lista de materiales, cortes y costos
  planos.pdf                           planos A3 (ISO 128, primer diedro): conjunto, madera, tubos
  explotado.pdf / explotado.png        vista explotada con códigos de pieza
  guia-montaje.pdf / guia-montaje.md   guía de montaje e instalación (A4)

Uso: python generar_salidas.py   (no requiere FreeCAD)
"""
import csv
import datetime
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

import geometria as g

AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, "..", "salidas")
os.makedirs(SAL, exist_ok=True)
HOY = datetime.date.today().isoformat()
PROYECTO = "Organizador de lavadora"
REV = "A"
KERF_TUBO = 4          # mm, mismo valor que config (kerf proveedor); conservador para corte manual
LARGO_TUBO = 6000      # PVC-T-1, catálogo
PRECIO_TUBO = 38900    # PVC-T-1, catálogo (Homecenter, 2026-11-22)
LARGO_LISTON_REF = None

PIEZAS = g.piezas()
CORTES = dict(g.longitudes_corte())
R_RUN = g.TEE["largo"] / 2
BRAZO_CODO = min(g.CODO["extremos"]) - g.CODO["de"] / 2


def desc_tubo(p):
    a, b = p["a"], p["b"]
    if a[0] == b[0] and a[1] == b[1]:
        return "Paral piso-estante 1" if a[2] < g.Z_EST1 else "Paral estante 1-estante 2"
    if a[2] == g.Z_PISO:
        return "Larguero piso (fondo)"
    return "Larguero estante 1 (ancho)" if a[2] == g.Z_EST1 else "Larguero estante 2 (ancho)"


def accesorio_en(punto):
    for p in PIEZAS:
        if p["tipo"] in ("tee", "codo") and all(abs(u - v) < 1e-6 for u, v in zip(p["centro"], punto)):
            return p["codigo"]
    return "?"


# ---------------------------------------------------------------- 1. BOM y despiece
def optimizar_barras(cortes, largo, kerf):
    """Primer ajuste decreciente."""
    barras = []
    for cod, L in sorted(cortes, key=lambda c: -c[1]):
        for b in barras:
            if b["libre"] >= L + kerf:
                b["piezas"].append((cod, L)); b["libre"] -= L + kerf
                break
        else:
            barras.append(dict(piezas=[(cod, L)], libre=largo - L - kerf))
    return barras


def generar_bom():
    tubos = [(c, L) for c, L in CORTES.items()]
    barras = optimizar_barras(tubos, LARGO_TUBO, KERF_TUBO)
    n_tee = sum(1 for p in PIEZAS if p["tipo"] == "tee")
    n_codo = sum(1 for p in PIEZAS if p["tipo"] == "codo")
    tableros = [p for p in PIEZAS if p["tipo"] == "tablero"]
    listones = [p for p in PIEZAS if p["tipo"] == "liston"]
    filas = []
    filas.append(dict(item="PVC-T-1", descripcion='Tubo PVC presión 1" RDE 13.5 x 6 m (Pavco)', cantidad=len(barras), unidad="tubo",
                      precio_unit=PRECIO_TUBO, fuente="catalogos/tubos_pvc.yaml"))
    filas.append(dict(item="PVC-TEE-1", descripcion='Tee 1" presión, para soldar', cantidad=n_tee, unidad="und", precio_unit=None, fuente="PENDIENTE precio"))
    filas.append(dict(item="PVC-COD-1", descripcion='Codo 90° 1" presión, para soldar', cantidad=n_codo, unidad="und", precio_unit=None, fuente="PENDIENTE precio y ficha"))
    filas.append(dict(item="TRX-15", descripcion="Triplex Refopanel 15 mm 1220 x 2440 (ya disponible)", cantidad=1, unidad="hoja", precio_unit=0,
                      fuente="usuario ya lo tiene; precio catálogo 130000"))
    filas.append(dict(item="LIS-18", descripcion=f"Listón 18 x {g.LISTON['ancho']} mm (material PENDIENTE)", cantidad=len(listones), unidad="und",
                      precio_unit=None, fuente="PENDIENTE"))
    for h in g.herrajes():
        filas.append(dict(item=h["codigo"], descripcion=h["descripcion"], cantidad=h["cantidad"], unidad="und", precio_unit=None, fuente="PENDIENTE modelo/precio"))
    filas.append(dict(item="ARA-1", descripcion="Arandela para TOR-1", cantidad=g.herrajes()[0]["cantidad"], unidad="und", precio_unit=None, fuente="PENDIENTE"))
    filas.append(dict(item="SOL-PVC", descripcion="Soldadura (cemento solvente) PVC", cantidad=None, unidad="tarro", precio_unit=None, fuente="PENDIENTE cantidad/precio"))
    filas.append(dict(item="SEL-BAR", descripcion="Sellador para madera + barniz (elección del usuario)", cantidad=None, unidad="-", precio_unit=None, fuente="usuario"))
    for f in filas:
        f["subtotal"] = (f["precio_unit"] * f["cantidad"]) if (f["precio_unit"] is not None and f["cantidad"] is not None) else None
    total_conocido = sum(f["subtotal"] for f in filas if f["subtotal"] is not None)

    with open(os.path.join(SAL, "bom.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item", "descripcion", "cantidad", "unidad", "precio_unit_cop", "subtotal_cop", "fuente"])
        for f in filas:
            w.writerow([f["item"], f["descripcion"], f["cantidad"] if f["cantidad"] is not None else "PENDIENTE", f["unidad"],
                        f["precio_unit"] if f["precio_unit"] is not None else "PENDIENTE",
                        f["subtotal"] if f["subtotal"] is not None else "", f["fuente"]])

    # Despiece madera
    madera = []
    for p in tableros + listones:
        L, A, E = sorted(p["dims"], reverse=True)
        madera.append((p["codigo"], L, A, E, "muescas" if p.get("muesca") else ""))

    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
        wb = Workbook()
        ws = wb.active; ws.title = "Materiales"
        ws.append(["Item", "Descripción", "Cantidad", "Unidad", "Precio unit. (COP)", "Subtotal (COP)", "Fuente"])
        for f in filas:
            ws.append([f["item"], f["descripcion"], f["cantidad"], f["unidad"], f["precio_unit"], f["subtotal"], f["fuente"]])
        ws.append([]); ws.append(["", "Total con precios conocidos", "", "", "", total_conocido, "faltan precios PENDIENTE"])
        ws2 = wb.create_sheet("Cortes tubo")
        ws2.append(["Código", "Descripción", "Largo de corte (mm)", "Accesorio extremo A", "Accesorio extremo B"])
        for p in PIEZAS:
            if p["tipo"] == "tubo":
                ws2.append([p["codigo"], desc_tubo(p), CORTES[p["codigo"]], accesorio_en(p["a"]), accesorio_en(p["b"])])
        ws2.append([]); ws2.append(["Barra", "Piezas", "Sobrante (mm)"])
        for i, b in enumerate(barras, 1):
            ws2.append([i, ", ".join(f"{c} ({L})" for c, L in b["piezas"]), round(b["libre"])])
        ws3 = wb.create_sheet("Despiece madera")
        ws3.append(["Código", "Largo (mm)", "Ancho (mm)", "Espesor (mm)", "Nota"])
        for m in madera:
            ws3.append(list(m))
        for s in (ws, ws2, ws3):
            for c in s[1]:
                c.font = Font(bold=True)
            for col in s.columns:
                s.column_dimensions[col[0].column_letter].width = max(12, min(70, max(len(str(c.value or "")) for c in col) + 2))
        wb.save(os.path.join(SAL, "bom.xlsx"))
    except ImportError:
        pass

    md = [f"# Lista de materiales y despiece: {PROYECTO}", "", f"Generado {HOY} desde `modelo/geometria.py`. Rev. {REV}.", "",
          "## Materiales", "", "| Item | Descripción | Cant. | Unidad | Precio unit. COP | Subtotal COP |", "|---|---|---|---|---|---|"]
    for f in filas:
        md.append(f"| {f['item']} | {f['descripcion']} | {f['cantidad'] if f['cantidad'] is not None else 'PENDIENTE'} | {f['unidad']} | "
                  f"{f'{f[chr(112)+"recio_unit"]:,}'.replace(',', '.') if f['precio_unit'] is not None else 'PENDIENTE'} | "
                  f"{f'{f[chr(115)+"ubtotal"]:,}'.replace(',', '.') if f['subtotal'] is not None else ''} |")
    md += ["", f"**Total con precios conocidos: ${total_conocido:,} COP**".replace(",", "."), "(faltan los precios marcados PENDIENTE).", "",
           "## Cortes de tubo PVC 1\"", "", "| Código | Descripción | Corte (mm) | Extremo A | Extremo B |", "|---|---|---|---|---|"]
    for p in PIEZAS:
        if p["tipo"] == "tubo":
            md.append(f"| {p['codigo']} | {desc_tubo(p)} | {CORTES[p['codigo']]} | {accesorio_en(p['a'])} | {accesorio_en(p['b'])} |")
    md += ["", f"Optimización en barras de {LARGO_TUBO} mm con {KERF_TUBO} mm por corte:", ""]
    for i, b in enumerate(barras, 1):
        md.append(f"- Barra {i}: " + ", ".join(f"{c} ({L})" for c, L in b["piezas"]) + f". Sobrante {round(b['libre'])} mm.")
    md += ["", "## Despiece de madera", "", "| Código | Largo | Ancho | Espesor | Nota |", "|---|---|---|---|---|"]
    for m in madera:
        md.append(f"| {m[0]} | {m[1]:.0f} | {m[2]:.0f} | {m[3]:.0f} | {m[4]} |")
    mx, mf, mb = g.muesca()
    md += ["", f"Muescas EST-01: {mx} x {mf} mm en las esquinas delanteras y {mx} x {mb} mm en las traseras.", "",
           "## Supuestos y pendientes", "",
           "- Precio de tee y codo 1\", listón (material), tornillos, arandelas, soldadura PVC y acabado: PENDIENTE.",
           f"- Campana del codo 1\" supuesta igual a la tee ({g.CAMPANA_CODO} mm); brazo del codo tomado del menor medido. Armar en seco y recortar.",
           f"- Kerf de {KERF_TUBO} mm aplicado también al corte de tubo (valor de la config para el proveedor).",
           "- El triplex ya lo tiene el usuario: costo 0 en el total."]
    with open(os.path.join(SAL, "despiece.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    return filas, barras, madera, total_conocido


# ---------------------------------------------------------------- 2. Planos A3
A3 = (420, 297)


def hoja(titulo, n, total, escala):
    fig = plt.figure(figsize=(A3[0] / 25.4, A3[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, A3[0]); ax.set_ylim(0, A3[1]); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((10, 10), A3[0] - 20, A3[1] - 20, fill=False, lw=0.8))
    # cajetín ISO 7200 simplificado (abajo a la derecha)
    x0, y0, w, h = A3[0] - 10 - 180, 10, 180, 36
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=0.8))
    for yy in (y0 + 12, y0 + 24):
        ax.plot([x0, x0 + w], [yy, yy], lw=0.4, color="k")
    for xx in (x0 + 60, x0 + 120):
        ax.plot([xx, xx], [y0, y0 + 24], lw=0.4, color="k")
    t = lambda x, y, s, **k: ax.text(x, y, s, fontsize=k.pop("fs", 6.5), va="center", **k)
    t(x0 + 2, y0 + 30, f"{PROYECTO}: {titulo}", fs=9, weight="bold")
    t(x0 + 2, y0 + 18, "Material: PVC 1\" RDE 13.5 / triplex 15 mm")
    t(x0 + 62, y0 + 18, f"Escala {escala}   Unidades: mm")
    t(x0 + 122, y0 + 18, "ISO 128 · primer diedro ⊕◯")
    t(x0 + 2, y0 + 6, f"Fecha {HOY}")
    t(x0 + 62, y0 + 6, f"Rev. {REV}   Hoja {n}/{total}")
    t(x0 + 122, y0 + 6, "Generado desde geometria.py")
    return fig, ax


def cota(ax, p1, p2, off, texto=None, vertical=False, fs=6):
    (x1, y1), (x2, y2) = p1, p2
    if vertical:
        xc = x1 + off
        ax.plot([x1, xc + np.sign(off) * 1.5], [y1, y1], lw=0.3, color="k"); ax.plot([x2, xc + np.sign(off) * 1.5], [y2, y2], lw=0.3, color="k")
        ax.annotate("", (xc, y1), (xc, y2), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
        ax.text(xc - 1.2 * np.sign(off) if off < 0 else xc + 1.2, (y1 + y2) / 2, texto, rotation=90, fontsize=fs, ha="center", va="center",
                bbox=dict(fc="white", ec="none", pad=0.2))
    else:
        yc = y1 + off
        ax.plot([x1, x1], [y1, yc + np.sign(off) * 1.5], lw=0.3, color="k"); ax.plot([x2, x2], [y2, yc + np.sign(off) * 1.5], lw=0.3, color="k")
        ax.annotate("", (x1, yc), (x2, yc), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
        ax.text((x1 + x2) / 2, yc, texto, fontsize=fs, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.2))


def proyectar(p, vista):
    """Devuelve lista de parches 2D (en mm del objeto) para la vista: 'frontal' (X,Z), 'lateral' (Y,Z), 'planta' (X,Y)."""
    ix, iy = {"frontal": (0, 2), "lateral": (1, 2), "planta": (0, 1)}[vista]
    r = g.TUBO_DE / 2
    out = []
    if p["tipo"] == "tubo":
        a, b = np.array(p["a"]), np.array(p["b"])
        u, v = (a[ix], a[iy]), (b[ix], b[iy])
        if abs(u[0] - v[0]) < 1e-6 and abs(u[1] - v[1]) < 1e-6:
            out.append(("circ", u, r))
        else:
            x0, x1 = sorted([u[0], v[0]]); y0, y1 = sorted([u[1], v[1]])
            if x1 - x0 < 1e-6:
                out.append(("rect", (x0 - r, y0), 2 * r, y1 - y0))
            else:
                out.append(("rect", (x0, y0 - r), x1 - x0, 2 * r))
    elif p["tipo"] in ("tee", "codo"):
        c = np.array(p["centro"]); rr = 20
        arm = R_RUN if p["tipo"] == "tee" else BRAZO_CODO
        for d in p["ramas"]:
            e = c + np.array(d) * arm
            u, v = (c[ix], c[iy]), (e[ix], e[iy])
            if abs(u[0] - v[0]) < 1e-6 and abs(u[1] - v[1]) < 1e-6:
                out.append(("circ", u, rr))
            else:
                x0, x1 = sorted([u[0], v[0]]); y0, y1 = sorted([u[1], v[1]])
                out.append(("rect", (x0 - rr, y0), 2 * rr, y1 - y0) if x1 - x0 < 1e-6 else ("rect", (x0, y0 - rr), x1 - x0, 2 * rr))
    else:
        o, d = p["origen"], p["dims"]
        if vista == "planta" and p.get("muesca"):
            mx, mf, mb = p["muesca"]
            x0, y0 = o[0], o[1]; x1, y1 = x0 + d[0], y0 + d[1]
            out.append(("poly", [(x0 + mx, y0), (x1 - mx, y0), (x1 - mx, y0 + mf), (x1, y0 + mf), (x1, y1 - mb), (x1 - mx, y1 - mb), (x1 - mx, y1),
                                 (x0 + mx, y1), (x0 + mx, y1 - mb), (x0, y1 - mb), (x0, y0 + mf), (x0 + mx, y0 + mf)]))
        else:
            out.append(("rect", (o[ix], o[iy]), d[ix], d[iy]))
    return out


COLORES = {"tubo": "#eceff1", "tee": "#b0bec5", "codo": "#b0bec5", "tablero": "#f3dfc1", "liston": "#d7b899"}


def dibujar_vista(ax, vista, ox, oy, esc, orden=None):
    piezas = PIEZAS if orden is None else orden
    for p in piezas:
        for parche in proyectar(p, vista):
            col = COLORES[p["tipo"]]
            if parche[0] == "rect":
                (x, y), w, h = parche[1], parche[2], parche[3]
                ax.add_patch(Rectangle((ox + x * esc, oy + y * esc), w * esc, h * esc, fc=col, ec="k", lw=0.35, alpha=0.9))
            elif parche[0] == "circ":
                (x, y), r = parche[1], parche[2]
                ax.add_patch(Circle((ox + x * esc, oy + y * esc), r * esc, fc=col, ec="k", lw=0.35))
            else:
                ax.add_patch(Polygon([(ox + x * esc, oy + y * esc) for x, y in parche[1]], closed=True, fc=col, ec="k", lw=0.35, alpha=0.9))


def orden_vista(vista):
    # dibujar primero lo que está más lejos del observador
    prof = {"frontal": 1, "lateral": 0, "planta": 2}[vista]
    signo = {"frontal": -1, "lateral": 1, "planta": 1}[vista]

    def clave(p):
        if p["tipo"] == "tubo":
            v = (p["a"][prof] + p["b"][prof]) / 2
        elif p["tipo"] in ("tee", "codo"):
            v = p["centro"][prof]
        else:
            v = p["origen"][prof] + p["dims"][prof] / 2
        return signo * v
    return sorted(PIEZAS, key=clave)


def generar_planos():
    esc = 1 / 10
    W = 2 * (g.CX + g.MARGEN_ESTANTE)
    xmin = -W / 2
    y_fr, _ = g.y_estante(1)
    y_back = g.y_panel() + g.TRIPLEX
    alto = g.Z_EST2 + R_RUN + g.TRIPLEX
    with PdfPages(os.path.join(SAL, "planos.pdf")) as pdf:
        # Hoja 1: conjunto
        esc = 1 / 15
        fig, ax = hoja("Conjunto", 1, 3, "1:15")
        fx, fy = 80, 125          # origen vista frontal (x=0,z=0 del objeto)
        lx = fx + W * esc / 2 + 60 + (y_back - y_fr) * esc / 2  # lateral izquierda a la derecha (primer diedro)
        dibujar_vista(ax, "frontal", fx, fy, esc, orden_vista("frontal"))
        dibujar_vista(ax, "lateral", lx, fy, esc, orden_vista("lateral"))
        px, py = fx, fy - 22 - (y_back) * esc  # planta debajo del frontal (primer diedro)
        dibujar_vista(ax, "planta", px, py, esc, orden_vista("planta"))
        cota(ax, (px + xmin * esc, py + y_fr * esc), (px + xmin * esc, py + y_back * esc), -8, f"{y_back - y_fr:.0f}", vertical=True)
        ax.text(fx, fy + alto * esc + 8, "VISTA FRONTAL", ha="center", fontsize=8, weight="bold")
        ax.text(lx, fy + alto * esc + 8, "VISTA LATERAL IZQUIERDA", ha="center", fontsize=8, weight="bold")
        ax.text(px + W * esc / 2 + 10, py, "PLANTA", fontsize=8, weight="bold", va="center")
        # cotas frontal
        cota(ax, (fx + xmin * esc, fy), (fx - xmin * esc, fy), -6, f"{W:.0f}")
        cota(ax, (fx + xmin * esc, fy), (fx + xmin * esc, fy + alto * esc), -8, f"{alto:.0f}", vertical=True)
        z1top = g.Z_EST1 + R_RUN + g.TRIPLEX
        cota(ax, (fx - xmin * esc, fy), (fx - xmin * esc, fy + (g.Z_EST1 - g.TUBO_DE / 2) * esc), 7, f"{g.Z_EST1 - g.TUBO_DE / 2:.0f} libre", vertical=True)
        cota(ax, (fx - xmin * esc, fy + z1top * esc), (fx - xmin * esc, fy + (g.Z_EST2 - R_RUN) * esc), 7, f"{g.Z_EST2 - R_RUN - z1top:.0f}", vertical=True)
        cota(ax, (fx - g.CX * esc, fy + 40), (fx + g.CX * esc, fy + 40), 0, f"{2 * g.CX} entre ejes")
        # cotas lateral
        cota(ax, (lx + y_fr * esc, fy), (lx + y_back * esc, fy), -6, f"{y_back - y_fr:.0f}")
        cota(ax, (lx - g.CY * esc, fy + 40), (lx + g.CY * esc, fy + 40), 0, f"{2 * g.CY} entre ejes")
        esc = 1 / 10
        ax.text(20, 280, "Notas:\n1. Cotas en mm, tomadas de geometria.py.\n2. Accesorios dibujados con medidas del usuario (aprox.).\n"
                f"3. Tapa abierta de la lavadora: {g.LAVADORA['alto_tapa_abierta']} mm; estante 1 libre a {g.Z_EST1 - g.TUBO_DE / 2:.0f} mm.",
                fontsize=6.5, va="top")
        pdf.savefig(fig); plt.close(fig)

        # Hoja 2: madera
        fig, ax = hoja("Piezas de madera", 2, 3, "1:10")
        e5 = 1 / 10
        est = {p["codigo"]: p for p in PIEZAS if p["tipo"] in ("tablero", "liston")}
        # EST-01
        p = est["EST-01"]; o, d = p["origen"], p["dims"]; mx, mf, mb = p["muesca"]
        bx, by = 40, 170
        pts = [(0 + mx, 0), (d[0] - mx, 0), (d[0] - mx, mf), (d[0], mf), (d[0], d[1] - mb), (d[0] - mx, d[1] - mb), (d[0] - mx, d[1]),
               (mx, d[1]), (mx, d[1] - mb), (0, d[1] - mb), (0, mf), (mx, mf)]
        ax.add_patch(Polygon([(bx + x * e5, by + y * e5) for x, y in pts], fc=COLORES["tablero"], ec="k", lw=0.5))
        ax.text(bx, by + d[1] * e5 + 10, "EST-01  Estante 1 (1 und, triplex 15)", fontsize=8, weight="bold")
        cota(ax, (bx, by), (bx + d[0] * e5, by), -7, f"{d[0]:.0f}")
        cota(ax, (bx, by), (bx, by + d[1] * e5), -7, f"{d[1]:.0f}", vertical=True)
        cota(ax, (bx, by + d[1] * e5), (bx + mx * e5, by + d[1] * e5), 5, f"{mx}")
        cota(ax, (bx + d[0] * e5, by), (bx + d[0] * e5, by + mf * e5), 6, f"{mf}", vertical=True)
        cota(ax, (bx + d[0] * e5, by + (d[1] - mb) * e5), (bx + d[0] * e5, by + d[1] * e5), 6, f"{mb}", vertical=True)
        ax.text(bx + d[0] * e5 / 2, by + d[1] * e5 / 2, "FRENTE abajo\nFONDO (pared) arriba", fontsize=6.5, ha="center", va="center")
        # EST-02
        p = est["EST-02"]; d = p["dims"]; bx2, by2 = 190, 170
        ax.add_patch(Rectangle((bx2, by2), d[0] * e5, d[1] * e5, fc=COLORES["tablero"], ec="k", lw=0.5))
        ax.text(bx2, by2 + d[1] * e5 + 10, "EST-02  Estante 2 / remate (1 und, triplex 15)", fontsize=8, weight="bold")
        cota(ax, (bx2, by2), (bx2 + d[0] * e5, by2), -7, f"{d[0]:.0f}")
        cota(ax, (bx2, by2), (bx2, by2 + d[1] * e5), -7, f"{d[1]:.0f}", vertical=True)
        # PAN-01
        p = est["PAN-01"]; d = p["dims"]; bx3, by3 = 40, 80
        ax.add_patch(Rectangle((bx3, by3), d[0] * e5, d[2] * e5, fc=COLORES["tablero"], ec="k", lw=0.5))
        ax.text(bx3, by3 + d[2] * e5 + 6, "PAN-01  Panel trasero (1 und, triplex 15)", fontsize=8, weight="bold")
        cota(ax, (bx3, by3), (bx3 + d[0] * e5, by3), -6, f"{d[0]:.0f}")
        cota(ax, (bx3, by3), (bx3, by3 + d[2] * e5), -7, f"{d[2]:.0f}", vertical=True)
        # Listones
        yy = 120
        ax.text(190, yy + 12, "Listones (sección 18 x 30)", fontsize=8, weight="bold")
        for c in ("LIS-01", "LIS-02", "LIS-03", "LIS-04"):
            d = est[c]["dims"]
            ax.add_patch(Rectangle((190, yy), d[0] * e5, 3, fc=COLORES["liston"], ec="k", lw=0.4))
            ax.text(190 + d[0] * e5 + 3, yy + 1.5, f"{c}: {d[0]:.0f} x {d[1]:.0f} x {d[2]:.0f}", fontsize=6.5, va="center")
            yy -= 9
        pdf.savefig(fig); plt.close(fig)

        # Hoja 3: tubos
        fig, ax = hoja("Estructura PVC y cortes", 3, 3, "1:10")
        dibujar_vista(ax, "frontal", 70, 70, esc, orden_vista("frontal"))
        dibujar_vista(ax, "lateral", 160, 70, esc, orden_vista("lateral"))
        for p in PIEZAS:
            if p["tipo"] == "tubo":
                a, b = np.array(p["a"]), np.array(p["b"]); m = (a + b) / 2
                if p["a"][1] == -g.CY or (p["a"][0] == p["b"][0] and p["a"][1] == p["b"][1] and p["a"][1] < 0):
                    if p["a"][1] < 0 or p["a"][2] != p["b"][2]:
                        ax.text(70 + m[0] * esc + 3, 70 + m[2] * esc, p["codigo"], fontsize=5.5, color="#b71c1c")
            if p["tipo"] in ("tee", "codo") and p["centro"][1] < 0:
                c = p["centro"]; ax.text(70 + c[0] * esc + 3, 70 + c[2] * esc - 4, p["codigo"], fontsize=5.5, color="#1a237e")
        ax.text(70, 70 + alto * esc + 8, "FRENTE (códigos del frente)", ha="center", fontsize=8, weight="bold")
        ax.text(160, 70 + alto * esc + 8, "LATERAL", ha="center", fontsize=8, weight="bold")
        tx, ty = 215, 270
        ax.text(tx, ty, "Tabla de cortes, tubo PVC 1\" RDE 13.5", fontsize=8, weight="bold")
        ty -= 7
        ax.text(tx, ty, "Código    Descripción                         Corte    Extremos", fontsize=6.5, family="monospace"); ty -= 5
        for p in PIEZAS:
            if p["tipo"] == "tubo":
                ax.text(tx, ty, f"{p['codigo']:<9} {desc_tubo(p):<35} {CORTES[p['codigo']]:>5}    {accesorio_en(p['a'])}/{accesorio_en(p['b'])}",
                        fontsize=6.2, family="monospace"); ty -= 4.6
        ty -= 4
        ax.text(tx, ty, f"Corte = distancia entre centros - (centro a fondo de campana) en cada extremo.\n"
                f"Tee: {R_RUN:.0f} - {g.CAMPANA_1} = {R_RUN - g.CAMPANA_1:.0f} mm.  Codo: {BRAZO_CODO:.0f} - {g.CAMPANA_CODO} = {BRAZO_CODO - g.CAMPANA_CODO:.0f} mm (campana supuesta).\n"
                "Armar en seco antes de soldar; recortar si sobra.", fontsize=6.2, va="top")
        pdf.savefig(fig); plt.close(fig)


# ---------------------------------------------------------------- 3. Vista explotada
def caja3d(ax, o, d, color, alpha=0.9, poly=None):
    x, y, z = o; dx, dy, dz = d
    if poly:
        n = len(poly); bot = [(px, py, z) for px, py in poly]; top = [(px, py, z + dz) for px, py in poly]
        caras = [bot, top] + [[bot[i], bot[(i + 1) % n], top[(i + 1) % n], top[i]] for i in range(n)]
    else:
        v = np.array([(x, y, z), (x + dx, y, z), (x + dx, y + dy, z), (x, y + dy, z), (x, y, z + dz), (x + dx, y, z + dz), (x + dx, y + dy, z + dz), (x, y + dy, z + dz)])
        caras = [v[c] for c in ([0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4])]
    ax.add_collection3d(Poly3DCollection(caras, facecolor=color, edgecolor="#5d4037", linewidths=0.4, alpha=alpha))


def cil3d(ax, a, b, r, color, n=16):
    a, b = np.array(a, float), np.array(b, float); d = b - a; L = np.linalg.norm(d); d /= L
    t = np.array([1, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1, 0])
    u = np.cross(d, t); u /= np.linalg.norm(u); w = np.cross(d, u)
    th = np.linspace(0, 2 * np.pi, n); TH, S = np.meshgrid(th, [0, L])
    P = a[:, None, None] + d[:, None, None] * S + r * (u[:, None, None] * np.cos(TH) + w[:, None, None] * np.sin(TH))
    ax.plot_surface(P[0], P[1], P[2], color=color, linewidth=0, shade=True)


def desplazamiento(p):
    """Separación por niveles de montaje (mm)."""
    if p["tipo"] == "tubo":
        a, b = p["a"], p["b"]
        if a[2] == b[2]:
            return {g.Z_PISO: 0, g.Z_EST1: 250, g.Z_EST2: 600}[a[2]]
        return 120 if a[2] == g.Z_PISO else 420
    if p["tipo"] in ("tee", "codo"):
        z = p["centro"][2]
        return {g.Z_PISO: 0, g.Z_EST1: 250, g.Z_EST2: 600}[z]
    if p["tipo"] == "liston":
        return 330 if p["origen"][2] < g.Z_EST2 else 680
    if p["codigo"] == "EST-01":
        return 420
    if p["codigo"] == "EST-02":
        return 780
    return 0


def generar_explotado():
    fig = plt.figure(figsize=(11.7, 16.5), dpi=150)  # A3 vertical
    fig.subplots_adjust(0, 0, 1, 0.95)
    ax = fig.add_subplot(111, projection="3d")
    etiquetas = []
    for p in PIEZAS:
        dz = desplazamiento(p)
        dy = 350 if p["codigo"] == "PAN-01" else 0
        if p["tipo"] == "tubo":
            a = np.array(p["a"]) + [0, 0, dz]; b = np.array(p["b"]) + [0, 0, dz]
            cil3d(ax, a, b, g.TUBO_DE / 2, "#eceff1"); m = (a + b) / 2
            if (p["a"][1] < 0 and p["a"][0] < 0) or (p["a"][2] == p["b"][2] and p["a"][0] < 0 and p["a"][1] < 0) or (p["a"][2] == g.Z_PISO and p["a"][0] < 0):
                etiquetas.append((m, p["codigo"]))
        elif p["tipo"] in ("tee", "codo"):
            c = np.array(p["centro"]) + [0, 0, dz]
            arm = R_RUN if p["tipo"] == "tee" else BRAZO_CODO
            for d in p["ramas"]:
                cil3d(ax, c, c + np.array(d) * arm, 20, "#90a4ae")
            if p["centro"][0] < 0 and p["centro"][1] < 0:
                etiquetas.append((c, p["codigo"]))
        else:
            o = np.array(p["origen"]) + [0, dy, dz]
            poly = None
            if p.get("muesca"):
                mx, mf, mb = p["muesca"]; x0, y0 = o[0], o[1]; x1, y1 = x0 + p["dims"][0], y0 + p["dims"][1]
                poly = [(x0 + mx, y0), (x1 - mx, y0), (x1 - mx, y0 + mf), (x1, y0 + mf), (x1, y1 - mb), (x1 - mx, y1 - mb), (x1 - mx, y1),
                        (x0 + mx, y1), (x0 + mx, y1 - mb), (x0, y1 - mb), (x0, y0 + mf), (x0 + mx, y0 + mf)]
            caja3d(ax, o, p["dims"], "#d7a86e" if p["tipo"] == "tablero" else "#a1887f", 0.85, poly)
            etiquetas.append((o + np.array(p["dims"]) * [0.5, 0.5, 1], p["codigo"]))
    # globos a la izquierda (piezas de estructura) o a la derecha (madera), con línea guía
    for pos, txt in etiquetas:
        lado = 1 if txt[:3] in ("EST", "PAN", "LIS") else -1
        tx = np.array([lado * 750, pos[1], pos[2]])
        ax.plot([pos[0], tx[0]], [pos[1], tx[1]], [pos[2], tx[2]], color="#b71c1c", lw=0.4)
        ax.text(*tx, txt, fontsize=8, color="#b71c1c", ha="left" if lado > 0 else "right", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#b71c1c", lw=0.5))
    ax.set_xlim(-800, 800); ax.set_ylim(-500, 800); ax.set_zlim(0, 2700); ax.set_box_aspect((1600, 1300, 2700))
    ax.view_init(18, -58); ax.set_axis_off()
    fig.suptitle(f"{PROYECTO}: vista explotada de montaje (Rev. {REV})\nCódigos iguales a planos, lista de materiales y guía", fontsize=12)
    fig.savefig(os.path.join(SAL, "explotado.png"), bbox_inches="tight")
    fig.savefig(os.path.join(SAL, "explotado.pdf"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- 4. Guía de montaje
def pasos_guia():
    mx, mf, mb = g.muesca()
    h = {x["codigo"]: x for x in g.herrajes()}
    cortes_txt = "; ".join(f"{c}: {L} mm" for c, L in CORTES.items())
    return [
        ("Antes de empezar",
         ["Herramientas: sierra caladora o circular, taladro con broca de 4,5 mm, destornillador, metro, escuadra, lija, lápiz.",
          "Consumibles: soldadura (cemento solvente) para PVC, sellador para madera y barniz.",
          "Trabaja en un lugar ventilado: la soldadura PVC y el barniz desprenden vapores."]),
        ("1. Cortar los tubos",
         [f"Corta los 14 tramos de tubo de 1\" según la tabla: {cortes_txt}.",
          "Marca cada tramo con su código (cinta o marcador). Lija las rebabas.",
          "Los cortes que llegan a un codo usan una campana supuesta de 22 mm: si sobra, recorta en el armado en seco."]),
        ("2. Preparar la madera",
         [f"Corta EST-01 ({PIEZAS_D['EST-01'][0]:.0f} x {PIEZAS_D['EST-01'][1]:.0f}), EST-02 ({PIEZAS_D['EST-02'][0]:.0f} x {PIEZAS_D['EST-02'][1]:.0f}) "
          f"y PAN-01 ({PIEZAS_D['PAN-01'][0]:.0f} x {PIEZAS_D['PAN-01'][2]:.0f}) del triplex de 15 mm.",
          f"En EST-01 corta con la caladora las muescas: {mx} x {mf} mm en las esquinas delanteras y {mx} x {mb} mm en las traseras (ver plano hoja 2).",
          "Corta los 4 listones (LIS-01 a LIS-04) según el plano hoja 2.",
          "Lija, aplica sellador y luego barniz a todas las piezas de madera ANTES de armar (zona húmeda). Deja secar según el fabricante."]),
        ("3. Armado en seco de la estructura",
         ["Base: une cada larguero del piso (TUB-09, TUB-10) con dos codos del piso, con las bocas libres hacia arriba.",
          "Mete los parales inferiores (1309 mm) en los codos del piso y pon una tee arriba de cada uno, con la salida lateral hacia el centro del mueble.",
          "Une las tees de adelante con un larguero de 694 mm y las de atrás con otro.",
          "Mete los parales superiores (424 mm) en las tees y remata con los codos de arriba, unidos por los largueros de 684 mm.",
          "Comprueba que no esté torcida: mide las dos diagonales de cada cara; deben ser iguales. Ajusta antes de soldar."]),
        ("4. Soldar las uniones",
         ["Desarma unión por unión, aplica soldadura PVC en el tubo y en la campana, y encaja girando un cuarto de vuelta.",
          "Vuelve a medir diagonales mientras la soldadura está fresca. Deja curar según el fabricante antes de cargar."]),
        ("5. Listones sobre los largueros",
         [f"En cada larguero de estante haz 2 huecos pasantes de {g.BROCA_PASO_TUBO} mm, de abajo hacia arriba, a 1/4 y 3/4 del largo.",
          f"Apoya el listón encima (entre las bocas de las tees o codos) y atorníllalo desde abajo con {h['TOR-1']['cantidad']} tornillos TOR-1 en total (1-3/4\" con arandela)."]),
        ("6. Estante 1",
         ["Baja EST-01 desde arriba: las muescas rodean los parales y el estante queda sobre las tees y los listones.",
          "Atornilla desde arriba al listón: 2 tornillos TOR-2 (1-1/4\") por listón."]),
        ("7. Panel trasero",
         ["Apoya PAN-01 detrás de los parales del fondo, desde el estante 1 hasta los codos de arriba.",
          f"Atorníllalo a los parales con {h['TOR-3']['cantidad']} tornillos TOR-3 (2\"), 2 por paral. La punta asoma ~2 mm por delante del paral."]),
        ("8. Estante 2",
         ["Pon EST-02 encima de los codos y listones de arriba, tapando el borde superior del panel.",
          "Atornilla desde arriba al listón: 2 tornillos TOR-2 por listón."]),
        ("9. Instalación",
         ["Coloca el mueble sobre la lavadora sin que la toque en ningún punto.",
          f"Abre la tapa por completo y confirma que pasa por debajo del estante 1 (tapa {g.LAVADORA['alto_tapa_abierta']} mm, estante libre a {g.Z_EST1 - g.TUBO_DE / 2:.0f} mm).",
          "Nivela el mueble. No se ancla a la pared (decisión del usuario).",
          "No se calculó una carga máxima: usa los estantes para productos de aseo como se definió y distribuye el peso."]),
        ("Supuestos y pendientes",
         ["Campana del codo 1\" supuesta en 22 mm (igual a la tee).",
          "Material del listón de 18 mm, modelo exacto de tornillos, arandelas y soldadura: PENDIENTE.",
          "Posición de tornillos (1/4 y 3/4 del listón) es una propuesta, no está modelada.",
          "Carga máxima de los estantes: no calculada."]),
    ]


PIEZAS_D = {p["codigo"]: p["dims"] for p in PIEZAS if p["tipo"] in ("tablero", "liston")}


def generar_guia(filas):
    pasos = pasos_guia()
    md = [f"# Guía de montaje e instalación: {PROYECTO}", "", f"Rev. {REV}, {HOY}. Ver `planos.pdf`, `explotado.pdf` y `despiece.md`.", ""]
    for t, items in pasos:
        md.append(f"## {t}"); md.append("")
        md += [f"- {i}" for i in items]; md.append("")
    with open(os.path.join(SAL, "guia-montaje.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    import textwrap
    A4 = (8.27, 11.69)
    with PdfPages(os.path.join(SAL, "guia-montaje.pdf")) as pdf:
        fig = plt.figure(figsize=A4)
        fig.text(0.5, 0.93, f"Guía de montaje e instalación\n{PROYECTO}", ha="center", fontsize=18, weight="bold")
        img = plt.imread(os.path.join(SAL, "explotado.png"))
        axi = fig.add_axes([0.12, 0.08, 0.76, 0.78]); axi.imshow(img); axi.axis("off")
        fig.text(0.5, 0.04, f"Rev. {REV} · {HOY} · medidas en mm", ha="center", fontsize=9)
        pdf.savefig(fig); plt.close(fig)
        y = None; fig = None
        for t, items in pasos:
            lineas = [(t, "h")] + [(l, "b") for i in items for l in textwrap.wrap("• " + i, 95)] + [("", "b")]
            if fig is None or y - 0.02 * len(lineas) < 0.06:
                if fig is not None:
                    pdf.savefig(fig); plt.close(fig)
                fig = plt.figure(figsize=A4); y = 0.95
            for txt, k in lineas:
                fig.text(0.07, y, txt, fontsize=12 if k == "h" else 9.5, weight="bold" if k == "h" else "normal", va="top")
                y -= 0.03 if k == "h" else 0.021
        pdf.savefig(fig); plt.close(fig)
        # página de detalle de uniones si existe
        det = os.path.join(SAL, "vista-detalle-uniones.png")
        if os.path.exists(det):
            fig = plt.figure(figsize=A4)
            fig.text(0.5, 0.95, "Detalle de uniones", ha="center", fontsize=14, weight="bold")
            axi = fig.add_axes([0.05, 0.3, 0.9, 0.6]); axi.imshow(plt.imread(det)); axi.axis("off")
            pdf.savefig(fig); plt.close(fig)


if __name__ == "__main__":
    filas, barras, madera, total = generar_bom()
    generar_planos()
    generar_explotado()
    generar_guia(filas)
    print(f"Barras de tubo: {len(barras)}; total con precios conocidos: {total} COP")
    for f in sorted(os.listdir(SAL)):
        print(" ", f, os.path.getsize(os.path.join(SAL, f)))
