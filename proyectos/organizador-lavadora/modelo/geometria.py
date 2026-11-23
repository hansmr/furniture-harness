"""Geometría paramétrica del organizador de lavadora (sin dependencias de FreeCAD).

La consumen: organizador_lavadora.py (FreeCAD) y vista_previa.py (render rápido).
Origen: centro del espacio en planta, z=0 en el piso. X = ancho, Y = fondo (+Y hacia la pared), Z = alto.
Valores marcados PROPUESTA requieren aprobación del usuario.
"""

# --- Datos verificados (ver brief.md / catalogos) ---
ESPACIO = dict(ancho=840, fondo=710, alto=2080)         # usuario
LAVADORA = dict(ancho=540, fondo=560, alto=850, alto_tapa_abierta=1240)  # LG WT9DPB + medida usuario
TUBO_DE = 33.40          # 1" RDE 13.5, Pavco
TEE = dict(de=40, largo=70, alto=60)   # tee 1", medido por el usuario (7 x 6 x 4 cm)
CODO = dict(de=40, extremos=(60, 65))  # codo 90° 1", medido por el usuario: 6 x 4 x 6,5 cm
# Brazo desde el eje = extremo - de/2 -> 40 y 45 mm. Se usa el menor (corte más largo; se ajusta en seco).
CAMPANA_CODO = 22        # SUPUESTO: igual a la tee (misma serie). Confirmar en armado en seco.
TRIPLEX = 15             # TRX-15
CAMPANA_1 = 22           # profundidad de campana tee 1", medido por el usuario
ENVASE_MAX = 350         # altura máxima de envases, usuario

# --- PROPUESTA (para aprobar) ---
CX = 360                 # mitad de distancia entre ejes de parales en X
CY = 295                 # mitad de distancia entre ejes de parales en Y
MARGEN_ESTANTE = 40      # del eje del paral al borde del estante
Z_EST1 = 1360            # eje de las tees del estante 1 (estante apoya en z+35)
Z_EST2 = 1815            # eje de las tees del estante 2
# Estante 2 es el remate superior: codos arriba, sin largueros por encima.
# Estantes SIN perforaciones (usuario 2026-11-22): van entre parales, apoyados en listones
# sobre los largueros. Fijación con tornillos que atraviesan el tubo (usuario 2026-11-22), sin abrazaderas.
HOLGURA_PARAL = 2        # holgura del estante contra el tubo/tee, por lado
VARIANTE_ESTANTE = "muescas"   # "muescas": 800 mm con muescas en esquinas (usuario 2026-11-22) | "entre_parales": 676 mm
TORNILLOS_TUBO_POR_LISTON = 2     # tubo -> listón, desde abajo
TORNILLOS_ESTANTE_POR_LISTON = 2  # estante -> listón, desde arriba
TORNILLOS_PANEL = 4               # panel -> parales del fondo, desde atrás
BROCA_PASO_TUBO = 4.5             # PROPUESTA: hueco pasante en el PVC para que el tornillo pase libre
LISTON = dict(alto=18, ancho=30)  # PROPUESTA: listón sobre larguero; material PENDIENTE
HOLGURA_ENVASE = 20
Z_PISO = TEE["de"] / 2   # eje de los codos del piso
HOLGURA_MANO = 100       # sobre la tapa abierta


def y_panel():
    """Cara delantera del panel trasero: apoyada contra el cuerpo de los accesorios (r = 20)."""
    return CY + TEE["de"] / 2


def y_estante(i):
    """(y_frente, y_fondo) de cada estante. El estante 1 termina contra el panel; el 2 lo tapa por encima."""
    y_fr = -(CY + MARGEN_ESTANTE)
    y_fo = y_panel() - 1 if i == 1 else y_panel() + TRIPLEX
    return y_fr, y_fo


def muesca():
    """(mx, my_frente, my_fondo) en mm: muescas del estante 1 para librar el paral que sigue hacia arriba."""
    lim = TUBO_DE / 2 + HOLGURA_PARAL
    y_fr, y_fo = y_estante(1)
    mx = MARGEN_ESTANTE + lim
    my_fr = (-(CY - lim)) - y_fr
    my_fo = y_fo - (CY - lim)
    return (round(mx), round(my_fr), round(my_fo))


def dims_estante():
    if VARIANTE_ESTANTE == "muescas":
        y_fr, y_fo = y_estante(1)
        return 2 * (CX + MARGEN_ESTANTE), y_fo - y_fr
    lx = 2 * (CX - TEE["de"] / 2 - HOLGURA_PARAL)     # cabe entre las tees de los parales
    ly = 2 * (CY + MARGEN_ESTANTE)                      # sobresale por delante y por detrás de los largueros
    return lx, ly


def piezas():
    """Lista de piezas: dict(codigo, tipo, ...). Tubos van entre centros de accesorios."""
    p = []
    r_run = TEE["largo"] / 2
    esquinas = [(sx * CX, sy * CY) for sy in (-1, 1) for sx in (-1, 1)]
    n = 1
    for (x, y) in esquinas:
        for z0, z1 in ((Z_PISO, Z_EST1), (Z_EST1, Z_EST2)):
            p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(x, y, z0), b=(x, y, z1), de=TUBO_DE)); n += 1
    for sx in (-1, 1):  # largueros de piso en Y
        p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(sx*CX, -CY, Z_PISO), b=(sx*CX, CY, Z_PISO), de=TUBO_DE)); n += 1
    for z in (Z_EST1, Z_EST2):  # largueros en X frente y fondo
        for sy in (-1, 1):
            p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(-CX, sy*CY, z), b=(CX, sy*CY, z), de=TUBO_DE)); n += 1
    k = 1
    for (x, y) in esquinas:
        p.append(dict(codigo=f"COD-{k:02d}", tipo="codo", centro=(x, y, Z_PISO), ramas=[(0, 0, 1), (0, -1 if y > 0 else 1, 0)])); k += 1
    for (x, y) in esquinas:
        p.append(dict(codigo=f"COD-{k:02d}", tipo="codo", centro=(x, y, Z_EST2), ramas=[(0, 0, -1), (-1 if x > 0 else 1, 0, 0)])); k += 1
    t = 1
    for (x, y) in esquinas:
        p.append(dict(codigo=f"TEE-{t:02d}", tipo="tee", centro=(x, y, Z_EST1), ramas=[(0, 0, 1), (0, 0, -1), (-1 if x > 0 else 1, 0, 0)])); t += 1
    lx, ly = dims_estante()
    l = 1
    for i, z in enumerate((Z_EST1, Z_EST2), 1):
        # Estante 1: el paral sigue hacia arriba -> muescas. Estante 2: arriba solo hay codos -> sin muescas.
        mus = muesca() if (VARIANTE_ESTANTE == "muescas" and i == 1) else None
        y_fr, y_fo = y_estante(i)
        p.append(dict(codigo=f"EST-{i:02d}", tipo="tablero", origen=(-lx/2, y_fr, z + r_run), dims=(lx, y_fo - y_fr, TRIPLEX),
                      perforaciones=[], muesca=mus))
        for sy in (-1, 1):  # listones sobre largueros, entre tees/codos
            brazo = TEE["largo"] / 2 if i == 1 else min(CODO["extremos"]) - CODO["de"] / 2
            largo = 2 * (CX - brazo) - 2 * HOLGURA_PARAL   # entre las bocas de tees (est. 1) o codos (est. 2)
            p.append(dict(codigo=f"LIS-{l:02d}", tipo="liston", origen=(-largo/2, sy*CY - LISTON["ancho"]/2, z + r_run - LISTON["alto"]),
                          dims=(largo, LISTON["ancho"], LISTON["alto"]), perforaciones=[])); l += 1
    y0 = y_panel()
    pan_x = 2 * (CX + MARGEN_ESTANTE)
    p.append(dict(codigo="PAN-01", tipo="tablero", origen=(-pan_x/2, y0, Z_EST1), dims=(pan_x, TRIPLEX, Z_EST2 - Z_EST1 + r_run), perforaciones=[]))
    return p


def herrajes():
    """Tornillos. Largos calculados con grosores del modelo; tipo/calibre exacto: PENDIENTE de catálogo."""
    n_lis = sum(1 for p in piezas() if p["tipo"] == "liston")
    pasa_tubo = TUBO_DE + LISTON["alto"]          # tubo + listón
    est_lis = TRIPLEX + LISTON["alto"]             # estante + listón
    pan_tubo = TRIPLEX + TUBO_DE                   # panel + paral
    return [
        dict(codigo="TOR-1", descripcion=f'Tornillo madera 2" (50,8 mm) tubo a listón; recorrido disponible {pasa_tubo:.1f} mm',
             cantidad=n_lis * TORNILLOS_TUBO_POR_LISTON, modelo="PENDIENTE"),
        dict(codigo="TOR-2", descripcion=f'Tornillo madera 1-1/4" (31,8 mm) estante a listón; recorrido disponible {est_lis:.1f} mm',
             cantidad=n_lis * TORNILLOS_ESTANTE_POR_LISTON, modelo="PENDIENTE"),
        dict(codigo="TOR-3", descripcion=f'Tornillo madera 2" (50,8 mm) panel a paral; atraviesa {pan_tubo:.1f} mm y la punta asoma ~{50.8 - pan_tubo:.1f} mm',
             cantidad=TORNILLOS_PANEL, modelo="PENDIENTE"),
    ]


def _desc_accesorio(punto):
    """Distancia del centro del accesorio al fondo de su campana, según qué accesorio hay en ese punto."""
    z = punto[2]
    if abs(z - Z_EST1) < 1e-6:
        return TEE["largo"] / 2 - CAMPANA_1
    brazo = min(CODO["extremos"]) - CODO["de"] / 2
    return brazo - CAMPANA_CODO


def longitudes_corte():
    """Longitud de corte = distancia entre centros - (centro a fondo de campana) en cada extremo."""
    out = []
    for p in piezas():
        if p["tipo"] != "tubo":
            continue
        a, b = p["a"], p["b"]
        L = sum((bi - ai) ** 2 for ai, bi in zip(a, b)) ** 0.5
        out.append((p["codigo"], round(L - _desc_accesorio(a) - _desc_accesorio(b))))
    return out


def verificaciones():
    """Comprobaciones contra datos verificados. Devuelve lista de (ok, texto)."""
    r = []
    lx, ly = dims_estante()
    ancho_total = 2 * (CX + MARGEN_ESTANTE)
    r.append((ancho_total <= ESPACIO["ancho"], f"Ancho total (panel) {ancho_total} <= espacio {ESPACIO['ancho']}"))
    fondo_total = (y_panel() + TRIPLEX) - y_estante(1)[0]
    r.append((fondo_total <= ESPACIO["fondo"], f"Fondo total {fondo_total:.0f} <= espacio {ESPACIO['fondo']}"))
    txt = f"Estante 1: {lx:.0f} x {ly:.0f} mm; estante 2: {lx:.0f} x {y_estante(2)[1] - y_estante(2)[0]:.0f} mm; sin perforaciones"
    if VARIANTE_ESTANTE == "muescas":
        mx, mf, mb = muesca()
        txt += f"; estante 1 con muescas {mx} x {mf} mm (frente) y {mx} x {mb} mm (fondo)"
    r.append((True, txt + " (INFORMATIVO)"))
    libre_x = 2 * CX - TEE["de"]
    r.append((libre_x > LAVADORA["ancho"], f"Paso libre entre parales {libre_x} > lavadora {LAVADORA['ancho']}"))
    bajo_est1 = Z_EST1 - TUBO_DE / 2
    r.append((bajo_est1 >= LAVADORA["alto_tapa_abierta"] + HOLGURA_MANO,
              f"Bajo larguero estante 1 {bajo_est1:.0f} >= tapa abierta {LAVADORA['alto_tapa_abierta']} + {HOLGURA_MANO}"))
    r_run = TEE["largo"] / 2
    top_est1 = Z_EST1 + r_run + TRIPLEX
    libre1 = (Z_EST2 - r_run) - top_est1
    r.append((libre1 >= ENVASE_MAX + HOLGURA_ENVASE, f"Altura libre estante 1 {libre1:.0f} >= envase {ENVASE_MAX} + {HOLGURA_ENVASE}"))
    top_est2 = Z_EST2 + r_run + TRIPLEX
    tope = top_est2
    r.append((tope < ESPACIO["alto"], f"Altura total {tope:.0f} < techo {ESPACIO['alto']}"))
    r.append((True, f"Altura libre sobre estante 2 hasta el techo: {ESPACIO['alto'] - top_est2:.0f} mm (INFORMATIVO)"))
    return r


if __name__ == "__main__":
    for ok, t in verificaciones():
        print("OK  " if ok else "FALTA", t)
    print("\nHerrajes:")
    for h in herrajes():
        print(f"  {h['codigo']}: {h['descripcion']} x {h['cantidad']} ({h['modelo']})")
    print("\nLongitudes de corte (mm):")
    for c, L in longitudes_corte():
        print(f"  {c}: {L}")
