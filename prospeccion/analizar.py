"""Calcula tasas de respuesta del experimento a partir de la planilla completada.

Uso: python3 analizar.py [prospectos.csv]
Cuenta como enviado/respondido cualquier valor que empiece por "s" (s, si, sí).
"""
import csv
import math
import sys
from collections import defaultdict

archivo = sys.argv[1] if len(sys.argv) > 1 else "prospectos.csv"
filas = list(csv.DictReader(open(archivo, encoding="utf-8-sig")))


def si(v):
    return v.strip().lower().startswith("s")


def wilson(k, n, z=1.96):
    """Intervalo de confianza 95 % para una proporción (sirve con muestras chicas)."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - m), min(1, c + m)


def tabla(clave, titulo):
    g = defaultdict(lambda: [0, 0, 0])
    for f in filas:
        if not si(f["enviado (s/n)"]):
            continue
        k = f[clave]
        g[k][0] += 1
        g[k][1] += si(f["respondio (s/n)"])
        g[k][2] += si(f["interesado (s/n)"])
    print(f"\n== {titulo} ==")
    print(f"{'grupo':<14}{'enviados':>9}{'respuestas':>11}{'tasa':>7}   IC 95 %        {'interesados':>11}")
    for k, (n, r, i) in sorted(g.items(), key=lambda x: -(x[1][1] / x[1][0] if x[1][0] else 0)):
        lo, hi = wilson(r, n)
        print(f"{k:<14}{n:>9}{r:>11}{r / n:>7.0%}   {lo:>4.0%} - {hi:<4.0%}   {i:>11}")


enviados = sum(si(f["enviado (s/n)"]) for f in filas)
print(f"Enviados: {enviados} de {len(filas)}")
tabla("nicho", "Por nicho")
tabla("variante_oferta", "Por oferta (A = servicio a medida, B = herramienta/SaaS)")
tabla("pais", "Por país")
tabla("dolor_detectado", "Por problema detectado")
print("\nSi los intervalos de dos grupos se solapan mucho, la diferencia todavía no es concluyente.")
