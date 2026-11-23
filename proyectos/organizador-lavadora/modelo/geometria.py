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
CAMPANA_1 = None         # PENDIENTE: profundidad de campana tee 1" -> necesaria para longitudes de corte

# --- PROPUESTA (para aprobar) ---
CX = 360                 # mitad de distancia entre ejes de parales en X
CY = 295                 # mitad de distancia entre ejes de parales en Y
MARGEN_ESTANTE = 40      # del eje del paral al borde del estante
Z_EST1 = 1360            # eje de las tees del estante 1 (estante apoya en z+35)
Z_EST2 = 1680            # eje de las tees del estante 2
Z_SUP = 1980             # eje de los codos superiores
Z_PISO = TEE["de"] / 2   # eje de los codos del piso
HOLGURA_MANO = 100       # sobre la tapa abierta


def piezas():
    """Lista de piezas: dict(codigo, tipo, ...). Tubos van entre centros de accesorios."""
    p = []
    r_run = TEE["largo"] / 2
    esquinas = [(sx * CX, sy * CY) for sy in (-1, 1) for sx in (-1, 1)]
    # Parales (4), tramos entre niveles
    niveles = [Z_PISO, Z_EST1, Z_EST2, Z_SUP]
    n = 1
    for (x, y) in esquinas:
        for z0, z1 in zip(niveles[:-1], niveles[1:]):
            p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(x, y, z0), b=(x, y, z1), de=TUBO_DE)); n += 1
    # Largueros de piso en Y (laterales), codo en cada esquina
    for sx in (-1, 1):
        p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(sx*CX, -CY, Z_PISO), b=(sx*CX, CY, Z_PISO), de=TUBO_DE)); n += 1
    # Largueros en X (frente y fondo) en estantes y arriba
    for z in (Z_EST1, Z_EST2, Z_SUP):
        for sy in (-1, 1):
            p.append(dict(codigo=f"TUB-{n:02d}", tipo="tubo", a=(-CX, sy*CY, z), b=(CX, sy*CY, z), de=TUBO_DE)); n += 1
    # Accesorios
    k = 1
    for (x, y) in esquinas:
        p.append(dict(codigo=f"COD-{k:02d}", tipo="codo", centro=(x, y, Z_PISO))); k += 1
    for (x, y) in esquinas:
        p.append(dict(codigo=f"COD-{k:02d}", tipo="codo", centro=(x, y, Z_SUP))); k += 1
    t = 1
    for z in (Z_EST1, Z_EST2):
        for (x, y) in esquinas:
            p.append(dict(codigo=f"TEE-{t:02d}", tipo="tee", centro=(x, y, z), de=TEE["de"], largo=TEE["largo"])); t += 1
    # Estantes: apoyan sobre la boca superior de las tees
    lx, ly = 2 * (CX + MARGEN_ESTANTE), 2 * (CY + MARGEN_ESTANTE)
    for i, z in enumerate((Z_EST1, Z_EST2), 1):
        p.append(dict(codigo=f"EST-{i:02d}", tipo="tablero", origen=(-lx/2, -ly/2, z + r_run), dims=(lx, ly, TRIPLEX),
                      perforaciones=[(sx*CX, sy*CY) for sx in (-1, 1) for sy in (-1, 1)]))
    # Panel trasero detrás de los parales del fondo, entre estante 1 y arriba
    y0 = CY + TUBO_DE / 2
    p.append(dict(codigo="PAN-01", tipo="tablero", origen=(-lx/2, y0, Z_EST1), dims=(lx, TRIPLEX, Z_SUP - Z_EST1), perforaciones=[]))
    return p


def verificaciones():
    """Comprobaciones contra datos verificados. Devuelve lista de (ok, texto)."""
    r = []
    lx, ly = 2 * (CX + MARGEN_ESTANTE), 2 * (CY + MARGEN_ESTANTE)
    r.append((lx <= ESPACIO["ancho"], f"Ancho estante {lx} <= espacio {ESPACIO['ancho']}"))
    r.append((ly + TRIPLEX <= ESPACIO["fondo"], f"Fondo estante+panel {ly + TRIPLEX} <= espacio {ESPACIO['fondo']}"))
    libre_x = 2 * CX - TEE["de"]
    r.append((libre_x > LAVADORA["ancho"], f"Paso libre entre parales {libre_x} > lavadora {LAVADORA['ancho']}"))
    bajo_est1 = Z_EST1 - TUBO_DE / 2
    r.append((bajo_est1 >= LAVADORA["alto_tapa_abierta"] + HOLGURA_MANO,
              f"Bajo larguero estante 1 {bajo_est1:.0f} >= tapa abierta {LAVADORA['alto_tapa_abierta']} + {HOLGURA_MANO}"))
    tope = Z_SUP + TEE["de"] / 2
    r.append((tope < ESPACIO["alto"], f"Altura total {tope:.0f} < techo {ESPACIO['alto']}"))
    r.append((CAMPANA_1 is not None, "Profundidad de campana tee 1\" conocida (necesaria para cortes)"))
    return r


if __name__ == "__main__":
    for ok, t in verificaciones():
        print("OK  " if ok else "FALTA", t)
