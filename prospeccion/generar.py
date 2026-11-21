"""Genera la planilla de prospectos con mensajes personalizados y links de WhatsApp.

Uso: python3 generar.py "Tu Nombre"
Salida: prospectos.csv (abrir en Google Sheets / Excel)
"""
import csv
import random
import re
import sys
import urllib.parse
from pathlib import Path

NOMBRE = sys.argv[1] if len(sys.argv) > 1 else "[TU NOMBRE]"
BASE = Path(__file__).parent

CIUDAD = {"AR": "Buenos Aires", "MX": "CDMX", "CL": "Santiago", "ES": "Madrid"}

# Qué automatizaría para cada nicho (servicio 1) y qué haría la herramienta (servicio 2)
NICHO = {
    "dentista": {
        "plural": "consultorios odontológicos",
        "auto": "recordatorios automáticos de turnos por WhatsApp para bajar las ausencias, y agenda online",
        "saas": "confirma los turnos por WhatsApp, avisa al paciente el día anterior y rellena los huecos de cancelaciones",
    },
    "inmobiliaria": {
        "plural": "inmobiliarias",
        "auto": "un asistente que responde al instante las consultas de los portales y WhatsApp, filtra interesados y agenda visitas",
        "saas": "responde las consultas de portales en segundos, califica al interesado y le agenda la visita sola",
    },
    "gimnasio": {
        "plural": "gimnasios",
        "auto": "avisos automáticos de vencimiento de cuota por WhatsApp y campañas para recuperar socios que dejaron de venir",
        "saas": "cobra y avisa vencimientos por WhatsApp y detecta socios a punto de abandonar para recuperarlos",
    },
    "taller": {
        "plural": "talleres",
        "auto": "avisos automáticos por WhatsApp cuando el auto está listo, presupuestos rápidos y recordatorios de service",
        "saas": "manda presupuestos y avisos de 'tu auto está listo' por WhatsApp y recuerda el próximo service a cada cliente",
    },
    "estetica": {
        "plural": "salones de belleza",
        "auto": "reservas online 24/7 conectadas a WhatsApp con recordatorios para que no falten las clientas",
        "saas": "toma reservas 24/7 por WhatsApp, manda recordatorios y llena los huecos libres de la agenda",
    },
}


def dolor(web, rating, reviews, claimed):
    """Problema concreto detectado en el perfil de Google Maps."""
    if rating < 4.0 and reviews >= 5:
        return "mala_reputacion"
    if web == "-":
        return "sin_web"
    if web in ("ig", "fb", "wa"):
        return "solo_redes"
    if web == "basic":
        return "web_basica"
    if not claimed:
        return "perfil_no_reclamado"
    return "ok"


GANCHO = {
    "mala_reputacion": "Vi que en Google tienen {rating} estrellas con {reviews} reseñas: responder rápido y hacer seguimiento a cada cliente es de lo que más ayuda a subir esa nota.",
    "sin_web": "Vi que tienen {reviews} reseñas en Google pero ninguna web enlazada: muchos clientes buscan, no encuentran dónde reservar o consultar y se van a otro.",
    "solo_redes": "Vi que en Google los enlazan solo a redes sociales: quien los encuentra no tiene dónde reservar o consultar directamente.",
    "web_basica": "Vi su perfil en Google ({rating} estrellas, {reviews} reseñas, muy bien) y que la web es bastante básica para el nivel del negocio.",
    "perfil_no_reclamado": "Vi que su ficha de Google ({reviews} reseñas) no está verificada por ustedes, así que no controlan lo que aparece ni responden reseñas.",
    "ok": "Vi su perfil en Google ({rating} estrellas, {reviews} reseñas), se nota que trabajan muy bien.",
}


def mensaje(pais, nicho, nombre, d, variante, rating, reviews):
    n = NICHO[nicho]
    vos = pais == "AR"
    gancho = GANCHO[d].format(rating=rating, reviews=reviews)
    saludo = f"Hola, ¿cómo {'andás' if vos else 'estás'}? Soy {NOMBRE}."
    if variante == "A":  # Servicio 1: implementación a medida
        cuerpo = (
            f"{gancho} Ayudo a {n['plural']} de {CIUDAD[pais]} con {n['auto']}. "
            f"Lo dejo funcionando en pocos días y {'pagás' if vos else 'pagas'} solo si te sirve. "
            f"¿Te interesa que te muestre cómo quedaría para {nombre}? Son 10 minutos."
        )
    else:  # Servicio 2: herramienta SaaS del nicho
        cuerpo = (
            f"{gancho} Estoy lanzando una herramienta para {n['plural']} que {n['saas']}. "
            f"Busco 5 negocios de {CIUDAD[pais]} para probarla gratis 30 días a cambio de su opinión. "
            f"¿{'Te sumás' if vos else 'Te interesa'}?"
        )
    texto = f"{saludo} {cuerpo}"
    # Vocabulario local
    if pais != "AR":
        texto = texto.replace("de turnos", "de citas").replace("los turnos", "las citas")
    if pais == "ES":
        texto = texto.replace("el auto", "el coche").replace("'tu auto", "'tu coche")
        texto = texto.replace("el próximo service", "la próxima revisión").replace("recordatorios de service", "recordatorios de revisión")
    elif pais != "AR":
        texto = texto.replace("el próximo service", "el próximo servicio").replace("recordatorios de service", "recordatorios de servicio")
    return texto


def es_movil(pais, tel):
    return {
        "AR": tel.startswith("549"),
        "MX": True,
        "CL": tel.startswith("569"),
        "ES": tel[2:3] in ("6", "7"),
    }[pais]


def main():
    filas = []
    for linea in (BASE / "raw.txt").read_text(encoding="utf-8").splitlines():
        if not linea.strip() or linea.startswith("#"):
            continue
        pais, nicho, nombre, tel, web, rating, reviews, claimed, cid = linea.split("|")
        filas.append(dict(
            pais=pais, nicho=nicho, nombre=nombre,
            tel=re.sub(r"\D", "", tel), web=web,
            rating=float(rating), reviews=int(reviews), claimed=claimed == "1", cid=cid,
        ))

    # Orden aleatorio fijo y variante A/B alternada dentro de cada nicho+país (diseño equilibrado)
    random.Random(42).shuffle(filas)
    contador = {}
    for f in filas:
        k = (f["pais"], f["nicho"])
        contador[k] = contador.get(k, 0) + 1
        f["variante"] = "A" if contador[k] % 2 else "B"

    with open(BASE / "prospectos.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow([
            "id", "pais", "ciudad", "nicho", "negocio", "telefono", "canal", "web",
            "rating", "reseñas", "dolor_detectado", "variante_oferta", "mensaje",
            "link_whatsapp", "google_maps",
            "enviado (s/n)", "fecha_envio", "respondio (s/n)", "interesado (s/n)", "reunion (s/n)", "venta (s/n)", "notas",
        ])
        for i, f in enumerate(filas, 1):
            d = dolor(f["web"], f["rating"], f["reviews"], f["claimed"])
            rating = f"{f['rating']:g}"
            msg = mensaje(f["pais"], f["nicho"], f["nombre"], d, f["variante"], rating, f["reviews"])
            movil = es_movil(f["pais"], f["tel"])
            canal = "whatsapp" if movil else "fijo: probar WhatsApp, si no llamar"
            wa = f"https://wa.me/{f['tel']}?text={urllib.parse.quote(msg)}"
            w.writerow([
                i, f["pais"], CIUDAD[f["pais"]], f["nicho"], f["nombre"], f"+{f['tel'][:2]} {f['tel'][2:]}", canal, f["web"],
                rating, f["reviews"], d, f["variante"], msg, wa,
                f"https://www.google.com/maps?cid={f['cid']}",
                "", "", "", "", "", "", "",
            ])
    print(f"{len(filas)} prospectos -> prospectos.csv")


if __name__ == "__main__":
    main()
