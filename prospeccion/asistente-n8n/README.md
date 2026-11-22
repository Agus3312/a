# Asistente de WhatsApp para inmobiliarias (n8n)

Flujo: **mensaje de WhatsApp → IA (Claude) con memoria por cliente → responde, califica, revisa el calendario, agenda la visita y anota el lead en Google Sheets.**

```
WhatsApp Trigger → ¿es texto? → Asistente (Claude + memoria + 3 herramientas) → responde por WhatsApp
                                        ├─ Ver disponibilidad (Google Calendar)
                                        ├─ Agendar visita    (Google Calendar)
                                        └─ Registrar lead     (Google Sheets "Selmar - Leads del asistente")
```

Archivo para importar: `selmar-asistente.json`. Lo probé en n8n 1.123: se importa sin errores y todos los tipos y versiones de nodo existen. Para regenerarlo, por ejemplo con otras propiedades o con otro cliente, edita `build_workflow.py` y ejecútalo.

## Puesta en marcha (unos 45 minutos)

1. **n8n**: usa tu instancia o una cuenta de n8n Cloud (tiene prueba gratis).
2. **WhatsApp (Meta)**, en developers.facebook.com:
   1. Crea una app de tipo *Business* y agrégale el producto **WhatsApp**.
   2. Meta te da **un número de prueba gratis**. En *API Setup*, agrega como destinatarios hasta 5 números verificados: el tuyo y, para la demo en vivo, el de Juan.
   3. En n8n crea dos credenciales:
      - *WhatsApp OAuth API* (App ID + App Secret), para el Trigger.
      - *WhatsApp API* (token de acceso + Business Account ID), para responder.
   4. Para que no venza cada 24 h, genera un token permanente con un *System User* en Business Manager.
3. **Claude**: crea una API key en console.anthropic.com y cárgala como credencial *Anthropic* en n8n.
4. **Google**: crea en n8n las credenciales *Google Calendar* y *Google Sheets* con tu cuenta. Comparte la planilla de leads con esa cuenta si es otra.
5. **Importa** `selmar-asistente.json` (Workflows → Import from file). Después:
   - Asigna las credenciales en cada nodo.
   - En *Ver disponibilidad* y *Agendar visita*, cambia `primary` por el email del calendario del corredor.
   - **Activa** el workflow.
6. **Prueba**: desde tu celular, escríbele al número de prueba "Hola, vi el depto de Lo Prado".

## Costos aproximados por mes (una inmobiliaria chica)
- Claude: unos USD 5 a 15, según el volumen de mensajes.
- WhatsApp: responder dentro de las 24 h después de que el cliente escribe no tiene costo de mensaje. Escribir primero (plantillas) cuesta centavos de dólar.
- n8n Cloud: desde unos USD 24, o casi gratis en un VPS propio. Un mismo n8n sirve para varios clientes.

## Para pasar a producción con un cliente real
- Conecta **su** número a la WhatsApp Business API (verificación del negocio en Meta, de días a 2 semanas). La "coexistencia" permite seguir usando la app en ese número.
- Mueve las propiedades a una planilla que el corredor actualice. Hoy están escritas en el prompt, dentro de `build_workflow.py`.
- Cambia la "Memoria por cliente" por *Postgres Chat Memory*: la memoria simple se borra si n8n se reinicia.
