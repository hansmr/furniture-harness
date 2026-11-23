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
# sobre los largueros y fijados con abrazaderas para tubo 1" atornilladas (modelo PENDIENTE).
HOLGURA_PARAL = 2        # holgura del estante contra el tubo/tee, por lado
VARIANTE_ESTANTE = "muescas"   # "muescas": 800 mm con muescas en esquinas (usuario 2026-11-22) | "entre_parales": 676 mm
ABRAZADERAS_POR_LISTON = 2
ABRAZADERAS_PANEL = 4
LISTON = dict(alto=18, ancho=30)  # PROPUESTA: listón sobre larguero; material PENDIENTE
HOLGURA_ENVASE = 20
Z_PISO = TEE["de"] / 2   # eje de los codos del piso
HOLGURA_MANO = 100       # sobre la tapa abierta


def muesca():
    """Tamaño de la muesca cuadrada en cada esquina del estante 1 (libra el paral que sigue hacia arriba)."""
    m = MARGEN_ESTANTE + TUBO_DE / 2 + HOLGURA_PARAL
    return (round(m), round(m))


def dims_estante():
    if VARIANTE_ESTANTE == "muescas":
        return 2 * (CX + MARGEN_ESTANTE), 2 * (CY + MARGEN_ESTANTE)
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
        p.append(dict(codigo=f"EST-{i:02d}", tipo="tablero", origen=(-lx/2, -ly/2, z + r_run), dims=(lx, ly, TRIPLEX),
                      perforaciones=[], muesca=mus))
        for sy in (-1, 1):  # listones sobre largueros, entre tees/codos
            largo = 2 * CX - TEE["de"]
            p.append(dict(codigo=f"LIS-{l:02d}", tipo="liston", origen=(-largo/2, sy*CY - LISTON["ancho"]/2, z + r_run - LISTON["alto"]),
                          dims=(largo, LISTON["ancho"], LISTON["alto"]), perforaciones=[])); l += 1
    y0 = CY + TUBO_DE / 2
    pan_x = 2 * (CX + MARGEN_ESTANTE)
    p.append(dict(codigo="PAN-01", tipo="tablero", origen=(-pan_x/2, y0, Z_EST1), dims=(pan_x, TRIPLEX, Z_EST2 - Z_EST1 + r_run), perforaciones=[]))
    return p


def herrajes():
    n_lis = sum(1 for p in piezas() if p["tipo"] == "liston")
    return [
        dict(codigo="ABR-1", descripcion='Abrazadera para tubo 1" (Ø ext. 33,4 mm), fijación con tornillo a madera', cantidad=n_lis * ABRAZADERAS_POR_LISTON + ABRAZADERAS_PANEL, modelo="PENDIENTE"),
        dict(codigo="TOR-1", descripcion="Tornillo para madera estante a listón", cantidad="PENDIENTE", modelo="PENDIENTE"),
    ]


def longitudes_corte():
    """Longitud de corte de cada tubo = distancia entre centros - 2*(centro a fondo de campana)."""
    c = TEE["largo"] / 2 - CAMPANA_1   # centro del accesorio al fondo de la campana (aprox. con medidas del usuario)
    out = []
    for p in piezas():
        if p["tipo"] != "tubo":
            continue
        a, b = p["a"], p["b"]
        L = sum((bi - ai) ** 2 for ai, bi in zip(a, b)) ** 0.5
        out.append((p["codigo"], round(L - 2 * c)))
    return out


def verificaciones():
    """Comprobaciones contra datos verificados. Devuelve lista de (ok, texto)."""
    r = []
    lx, ly = dims_estante()
    ancho_total = 2 * (CX + MARGEN_ESTANTE)
    r.append((ancho_total <= ESPACIO["ancho"], f"Ancho total (panel) {ancho_total} <= espacio {ESPACIO['ancho']}"))
    r.append((ly + TRIPLEX <= ESPACIO["fondo"], f"Fondo estante+panel {ly + TRIPLEX} <= espacio {ESPACIO['fondo']}"))
    txt = f"Estante {lx:.0f} x {ly:.0f} mm, sin perforaciones"
    if VARIANTE_ESTANTE == "muescas":
        txt += f"; estante 1 con muescas de {muesca()[0]} x {muesca()[1]} mm en las 4 esquinas"
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
