# Lista de materiales y despiece: Organizador de lavadora

Generado 2026-11-23 desde `modelo/geometria.py`. Rev. B.

## Materiales

| Item | Descripción | Cant. | Unidad | Precio unit. COP | Subtotal COP |
|---|---|---|---|---|---|
| PVC-T-1 | Tubo PVC presión 1" RDE 13.5 x 6 m (Pavco) | 2 | tubo | 38.900 | 77.800 |
| PVC-TEE-1 | Tee 1" presión, para soldar | 4 | und | PENDIENTE |  |
| PVC-COD-1 | Codo 90° 1" presión, para soldar (Pavco, 04755) | 8 | und | 2.100 | 16.800 |
| TRX-15 | Triplex Refopanel 15 mm 1220 x 2440 (ya disponible) | 1 | hoja | 0 | 0 |
| LIS-18 | Listón 18 x 30 mm (material PENDIENTE) | 4 | und | PENDIENTE |  |
| TOR-1 | Tornillo madera 1-3/4" (44,5 mm) + arandela, tubo a listón; recorrido disponible 51.4 mm (entra ~11 mm en el listón) | 8 | und | PENDIENTE |  |
| TOR-2 | Tornillo madera 1-1/4" (31,8 mm) estante a listón; recorrido disponible 33.0 mm | 8 | und | PENDIENTE |  |
| TOR-3 | Tornillo madera 2" (50,8 mm) panel/diagonal a paral; atraviesa 48.4 mm y la punta asoma ~2.4 mm | 8 | und | PENDIENTE |  |
| ESC-1 | Escuadra metálica antivuelco paral trasero a pared, con tornillos y chazos para el muro | 2 | und | PENDIENTE |  |
| ARA-1 | Arandela para TOR-1 | 8 | und | PENDIENTE |  |
| SOL-PVC-946 | Soldadura PVC Soldaya 1/4 gal (946 cc), Soldacol; rinde ~215 uniones de 1" | 1 | tarro | 53.900 | 53.900 |
| SEL-BAR | Sellador para madera + barniz (elección del usuario) | PENDIENTE | - | PENDIENTE |  |

**Total con precios conocidos: $148.500 COP**
(faltan los precios marcados PENDIENTE).

## Cortes de tubo PVC 1"

| Código | Descripción | Corte (mm) | Extremo A | Extremo B |
|---|---|---|---|---|
| TUB-01 | Paral piso-estante 1 | 1309 | COD-01 | TEE-01 |
| TUB-02 | Paral estante 1-estante 2 | 424 | TEE-01 | COD-05 |
| TUB-03 | Paral piso-estante 1 | 1309 | COD-02 | TEE-02 |
| TUB-04 | Paral estante 1-estante 2 | 424 | TEE-02 | COD-06 |
| TUB-05 | Paral piso-estante 1 | 1309 | COD-03 | TEE-03 |
| TUB-06 | Paral estante 1-estante 2 | 424 | TEE-03 | COD-07 |
| TUB-07 | Paral piso-estante 1 | 1309 | COD-04 | TEE-04 |
| TUB-08 | Paral estante 1-estante 2 | 424 | TEE-04 | COD-08 |
| TUB-09 | Larguero piso (fondo) | 554 | COD-01 | COD-03 |
| TUB-10 | Larguero piso (fondo) | 554 | COD-02 | COD-04 |
| TUB-11 | Larguero estante 1 (ancho) | 694 | TEE-01 | TEE-02 |
| TUB-12 | Larguero estante 1 (ancho) | 694 | TEE-03 | TEE-04 |
| TUB-13 | Larguero estante 2 (ancho) | 684 | COD-05 | COD-06 |
| TUB-14 | Larguero estante 2 (ancho) | 684 | COD-07 | COD-08 |

Optimización en barras de 6000 mm con 4 mm por corte:

- Barra 1: TUB-01 (1309), TUB-03 (1309), TUB-05 (1309), TUB-07 (1309), TUB-11 (694). Sobrante 50 mm.
- Barra 2: TUB-12 (694), TUB-13 (684), TUB-14 (684), TUB-09 (554), TUB-10 (554), TUB-02 (424), TUB-04 (424), TUB-06 (424), TUB-08 (424). Sobrante 1098 mm.

## Despiece de madera

| Código | Largo | Ancho | Espesor | Nota |
|---|---|---|---|---|
| EST-01 | 800 | 649 | 15 | muescas |
| EST-02 | 800 | 665 | 15 |  |
| PAN-01 | 800 | 490 | 15 |  |
| LIS-01 | 646 | 30 | 18 |  |
| LIS-02 | 646 | 30 | 18 |  |
| LIS-03 | 636 | 30 | 18 |  |
| LIS-04 | 636 | 30 | 18 |  |
| DIA-01 | 1439 | 60 | 15 | extremos cortados a plomo (26.6° respecto al largo) |
| DIA-02 | 1439 | 60 | 15 | extremos cortados a plomo (26.6° respecto al largo) |

Muescas EST-01: 59 x 59 mm en las esquinas delanteras y 59 x 38 mm en las traseras.

## Supuestos y pendientes

- Precio de tee 1", listón (material), tornillos, arandelas, escuadras y acabado: PENDIENTE.
- Campana del codo 1" supuesta igual a la tee (22 mm); brazo del codo tomado del menor medido. Armar en seco y recortar.
- Kerf de 4 mm aplicado también al corte de tubo (valor de la config para el proveedor).
- El triplex ya lo tiene el usuario: costo 0 en el total.
