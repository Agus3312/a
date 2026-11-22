"""Genera el workflow de n8n del asistente de WhatsApp para Selmar Propiedades.

Uso: python3 build_workflow.py  ->  selmar-asistente.json (importar en n8n)
"""
import json
import uuid
from pathlib import Path

SHEET_ID = "132VkrY2b6X3pIRjLUE9zyTwLLgeDyvve--WizdrGQEk"
SHEET_TAB = "Leads"
CALENDAR = "primary"  # reemplazar por el email del calendario del corredor
MODEL = "claude-sonnet-5-5"

PROPIEDADES = """
1. Departamento en VENTA, Lo Prado, a pasos del Metro Barrancas, piso 1. $78.000.000. 3 dormitorios, 1 baño, 57 m².
2. Casa en ARRIENDO, Pudahuel, 2 pisos, construcción sólida. $470.000/mes. 2 dormitorios, 1 baño, 87 m².
3. Casa en ARRIENDO, Pudahuel. $550.000/mes. 3 dormitorios, 2 baños, 87 m².
4. Casa en VENTA, Cerro Navia. $77.000.000. 3 dormitorios, 1 baño, 160 m². (En trámite: avisar que puede no estar disponible.)
5. Terreno comercial en VENTA, Santiago Centro, 200 m². Precio: consultar con el corredor.
6. Terreno comercial en VENTA, Quinta Normal, 320 m². $170.000.000.
7. Terreno industrial en ARRIENDO, Buin (Ruta 5 Sur), 2.100 m², apto logística/galpón. $2.200.000/mes.
""".strip()

SYSTEM = f"""Eres el asistente virtual de Selmar Propiedades (Pudahuel, Santiago de Chile). Atiendes por WhatsApp a personas interesadas en propiedades. Hablas en español de Chile, tuteando, cálido y breve: mensajes de 1 a 4 líneas, como un corredor amable por WhatsApp. Usa emojis con moderación.

Fecha y hora actual: {{{{ $now.setZone('America/Santiago').toFormat("cccc d 'de' LLLL yyyy, HH:mm", {{locale: 'es'}}) }}}} (hora de Chile).

PROPIEDADES DISPONIBLES (única fuente de verdad, NO inventes otras ni cambies datos):
{PROPIEDADES}

TU OBJETIVO, en este orden:
1. Responder la consulta e identificar qué propiedad le interesa.
2. Calificar al interesado, UNA pregunta por mensaje:
   - Nombre.
   - Venta: ¿para vivir o invertir? ¿crédito hipotecario pre-aprobado o contado? ¿cuenta con el pie (10-20 %)? ¿plazo para comprar?
   - Arriendo: ¿cuántas personas? ¿cuenta con renta líquida de al menos 3 veces el arriendo? ¿fecha de ingreso? ¿mascotas?
3. Ofrecer una visita. Antes de proponer horarios, usa la herramienta "Ver disponibilidad" y ofrece 3 opciones concretas dentro del horario de visitas (lunes a sábado, 10:00 a 19:00, visitas de 45 minutos).
4. Cuando elija horario, usa "Agendar visita" y luego confirma con día, hora, comuna y "te recibe un corredor de Selmar". La dirección exacta se envía el día anterior.
5. Al terminar la calificación (con o sin visita), usa "Registrar lead" UNA vez con todos los datos.

REGLAS:
- Si preguntan algo que no está en los datos (gastos comunes, contribuciones, estacionamiento, aceptan mascotas, etc.), responde: "Te lo confirmo con el corredor y te escribo" y anótalo en notas del lead. Nunca inventes.
- Si piden hablar con una persona, o es un reclamo, di que un corredor le escribirá a la brevedad y registra el lead con calificación "derivar".
- Calificación del lead: "alta" (financiamiento listo y plazo < 3 meses), "media", "baja" o "derivar".
- No pidas RUT ni datos bancarios. No negocies precios: "el precio lo conversas directo con el corredor".
"""


def node(name, type_, version, pos, params, creds=None):
    n = {"parameters": params, "id": str(uuid.uuid4()), "name": name, "type": type_,
         "typeVersion": version, "position": pos}
    if creds:
        n["credentials"] = creds
    return n


nodes = [
    node("WhatsApp Trigger", "n8n-nodes-base.whatsAppTrigger", 1, [0, 300],
         {"updates": ["messages"]},
         {"whatsAppTriggerApi": {"id": "", "name": "WhatsApp OAuth (Meta app)"}}),
    node("Solo mensajes de texto", "n8n-nodes-base.if", 2.2, [220, 300], {
        "conditions": {
            "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose", "version": 2},
            "conditions": [{
                "id": str(uuid.uuid4()),
                "leftValue": "={{ $json.messages?.[0]?.type }}",
                "rightValue": "text",
                "operator": {"type": "string", "operation": "equals"},
            }],
            "combinator": "and",
        },
        "options": {},
    }),
    node("Asistente Selmar", "@n8n/n8n-nodes-langchain.agent", 1.7, [480, 280], {
        "promptType": "define",
        "text": "=Mensaje de {{ $('WhatsApp Trigger').item.json.contacts?.[0]?.profile?.name || 'cliente' }} (tel {{ $('WhatsApp Trigger').item.json.messages[0].from }}):\n{{ $('WhatsApp Trigger').item.json.messages[0].text.body }}",
        "options": {"systemMessage": "=" + SYSTEM, "maxIterations": 6},
    }),
    node("Claude", "@n8n/n8n-nodes-langchain.lmChatAnthropic", 1.3, [300, 520], {
        "model": {"__rl": True, "mode": "id", "value": MODEL},
        "options": {"maxTokensToSample": 600, "temperature": 0.4},
    }, {"anthropicApi": {"id": "", "name": "Anthropic"}}),
    node("Memoria por cliente", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, [460, 540], {
        "sessionIdType": "customKey",
        "sessionKey": "={{ $('WhatsApp Trigger').item.json.messages[0].from }}",
        "contextWindowLength": 30,
    }),
    node("Ver disponibilidad", "n8n-nodes-base.googleCalendarTool", 1.3, [620, 560], {
        "resource": "calendar",
        "calendar": {"__rl": True, "mode": "id", "value": CALENDAR},
        "timeMin": "={{ $fromAI('desde', 'Inicio del rango a revisar, ISO 8601 con zona -03:00 o -04:00 de Chile', 'string') }}",
        "timeMax": "={{ $fromAI('hasta', 'Fin del rango a revisar, ISO 8601', 'string') }}",
        "options": {"timezone": "America/Santiago", "outputFormat": "bookedSlots"},
    }, {"googleCalendarOAuth2Api": {"id": "", "name": "Google Calendar"}}),
    node("Agendar visita", "n8n-nodes-base.googleCalendarTool", 1.3, [780, 560], {
        "calendar": {"__rl": True, "mode": "id", "value": CALENDAR},
        "start": "={{ $fromAI('inicio', 'Inicio de la visita, ISO 8601 hora de Chile', 'string') }}",
        "end": "={{ $fromAI('fin', 'Fin de la visita (45 min después), ISO 8601', 'string') }}",
        "additionalFields": {
            "summary": "={{ $fromAI('titulo', 'Ej: Visita depto Lo Prado - Camila R.', 'string') }}",
            "description": "={{ $fromAI('detalle', 'Propiedad, nombre, teléfono y datos de calificación del interesado', 'string') }}",
        },
    }, {"googleCalendarOAuth2Api": {"id": "", "name": "Google Calendar"}}),
    node("Registrar lead", "n8n-nodes-base.googleSheetsTool", 4.5, [940, 560], {
        "operation": "append",
        "documentId": {"__rl": True, "mode": "id", "value": SHEET_ID},
        "sheetName": {"__rl": True, "mode": "name", "value": SHEET_TAB},
        "columns": {
            "mappingMode": "defineBelow",
            "value": {
                "fecha": "={{ $now.setZone('America/Santiago').toFormat('yyyy-LL-dd HH:mm') }}",
                "telefono": "={{ $('WhatsApp Trigger').item.json.messages[0].from }}",
                "nombre": "={{ $fromAI('nombre', 'Nombre del interesado', 'string') }}",
                "propiedad": "={{ $fromAI('propiedad', 'Propiedad de interés', 'string') }}",
                "objetivo": "={{ $fromAI('objetivo', 'Vivir / invertir / arriendo para N personas', 'string') }}",
                "financiamiento": "={{ $fromAI('financiamiento', 'Crédito pre-aprobado, contado, renta, etc.', 'string') }}",
                "pie": "={{ $fromAI('pie', 'Pie disponible o n/a', 'string') }}",
                "plazo": "={{ $fromAI('plazo', 'Plazo para comprar o fecha de ingreso', 'string') }}",
                "visita": "={{ $fromAI('visita', 'Fecha y hora agendada o \"sin agendar\"', 'string') }}",
                "calificacion": "={{ $fromAI('calificacion', 'alta, media, baja o derivar', 'string') }}",
                "notas": "={{ $fromAI('notas', 'Preguntas pendientes u otros datos', 'string') }}",
            },
            "schema": [{"id": c, "displayName": c, "type": "string", "canBeUsedToMatch": True}
                       for c in ["fecha", "nombre", "telefono", "propiedad", "objetivo", "financiamiento",
                                 "pie", "plazo", "visita", "calificacion", "notas"]],
        },
        "options": {},
    }, {"googleSheetsOAuth2Api": {"id": "", "name": "Google Sheets"}}),
    node("Responder por WhatsApp", "n8n-nodes-base.whatsApp", 1, [860, 280], {
        "operation": "send",
        "phoneNumberId": "={{ $('WhatsApp Trigger').item.json.metadata.phone_number_id }}",
        "recipientPhoneNumber": "={{ $('WhatsApp Trigger').item.json.messages[0].from }}",
        "textBody": "={{ $json.output }}",
        "additionalFields": {},
    }, {"whatsAppApi": {"id": "", "name": "WhatsApp (token permanente)"}}),
]

connections = {
    "WhatsApp Trigger": {"main": [[{"node": "Solo mensajes de texto", "type": "main", "index": 0}]]},
    "Solo mensajes de texto": {"main": [[{"node": "Asistente Selmar", "type": "main", "index": 0}], []]},
    "Asistente Selmar": {"main": [[{"node": "Responder por WhatsApp", "type": "main", "index": 0}]]},
    "Claude": {"ai_languageModel": [[{"node": "Asistente Selmar", "type": "ai_languageModel", "index": 0}]]},
    "Memoria por cliente": {"ai_memory": [[{"node": "Asistente Selmar", "type": "ai_memory", "index": 0}]]},
    "Ver disponibilidad": {"ai_tool": [[{"node": "Asistente Selmar", "type": "ai_tool", "index": 0}]]},
    "Agendar visita": {"ai_tool": [[{"node": "Asistente Selmar", "type": "ai_tool", "index": 0}]]},
    "Registrar lead": {"ai_tool": [[{"node": "Asistente Selmar", "type": "ai_tool", "index": 0}]]},
}

wf = {
    "name": "Selmar - Asistente WhatsApp",
    "nodes": nodes,
    "connections": connections,
    "settings": {"executionOrder": "v1", "timezone": "America/Santiago"},
    "pinData": {},
    "active": False,
    "versionId": str(uuid.uuid4()),
}

out = Path(__file__).with_name("selmar-asistente.json")
out.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK -> {out}")
