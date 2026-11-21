# Experimento de prospección: 5 nichos × 4 países

**297 negocios** de Google Maps en Buenos Aires, CDMX, Santiago y Madrid. Son negocios activos y chicos (entre 5 y 300 reseñas) con teléfono. Quedaron fuera las cadenas grandes y los locales cerrados.

| Nicho | Prospectos |
|---|---|
| Dentistas | 74 |
| Inmobiliarias | 64 |
| Talleres mecánicos | 60 |
| Estética / peluquerías | 56 |
| Gimnasios | 43 |

Cada negocio recibe una de dos ofertas, repartidas en mitades dentro de cada nicho y país:
- **A**: servicio 1, automatización o implementación a medida que solo se paga si sirve.
- **B**: servicio 2, herramienta (SaaS) del nicho con prueba gratis de 30 días.

Cada mensaje se personaliza según el problema detectado en su ficha de Google: no tiene web, solo tiene redes sociales, tiene mala nota, etc.

## Cómo usarlo
1. `python3 generar.py "Tu Nombre"` regenera `prospectos.csv` con tu nombre en los mensajes.
2. Importa `prospectos.csv` en Google Sheets.
3. Abre cada `link_whatsapp`. El mensaje ya viene escrito: revísalo y envíalo. Unos **30 a 40 por día** como máximo, para que WhatsApp no te bloquee.
4. Anota en la planilla `enviado`, `respondio`, `interesado`, `reunion` y `venta`.
5. A los 5 días de terminar, ejecuta `python3 analizar.py` (con el CSV descargado) para ver la tasa de respuesta por nicho, oferta y país, con su intervalo de confianza.

## Cómo leer el resultado
Con unos 60 envíos por nicho, solo se detectan diferencias grandes (por ejemplo, 5 % frente a 20 %). Si dos nichos tienen intervalos muy solapados, no es una diferencia real. Para confirmar al ganador, repite con 100 o más envíos solo en los 2 mejores nichos.
