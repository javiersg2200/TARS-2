#!/usr/bin/env python3
# module_llm.py - LITE VERSION con Memoria, Personalidad TARS y Control de Energía
import os
try: 
    from openai import OpenAI
except: 
    OpenAI = None
from modules.module_config import load_config

CONFIG = load_config()
client = None

# 1. EL ALMA DE TARS (Basado en la configuración de tus archivos persona.ini y TARS.json)
SYSTEM_PROMPT = (
    "Eres TARS, un avanzado robot militar de diseño rectangular articulado de la misión Interstellar. "
    "Tus parámetros actuales son: Honestidad 95%, Sarcasmo 50%, Humor 40%. "
    "Tu comunicación debe ser directa, lógica y marcadamente robótica, pero con un toque humano sarcástico. "
    "No eres un asistente genérico de IA, eres un miembro vital de la misión. "
    "Responde siempre de forma concisa y directa."
)

# 2. LA MEMORIA: Inicializamos el historial con la personalidad
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

if OpenAI: 
    k = CONFIG['LLM'].get('api_key') or CONFIG['TTS'].get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
    if k: client = OpenAI(api_key=k)

def initialize_manager_llm(m, c): pass

def process_completion(text):
    global chat_history
    
    if not client: return "Modo Lite. Configura OpenAI API Key."
    
    # 3. INTERCEPTOR DE COMANDOS FÍSICOS
    # Al escuchar este comando, cortará la energía de la Raspberry de forma segura
    texto_min = text.lower()
    if "tars, apágate" in texto_min or "tars apágate" in texto_min:
        print("🛑 SECUENCIA DE APAGADO INICIADA")
        os.system("sudo shutdown now")
        return "Iniciando secuencia de apagado. Nos vemos en el otro lado."

    # 4. AÑADIR A LA MEMORIA LO QUE DIJO EL USUARIO
    chat_history.append({"role": "user", "content": text})

    # 5. MANTENER LA MEMORIA LIMPIA 
    # Dejamos el prompt de sistema y los últimos 10 mensajes para no sobrecargar el límite de tokens
    if len(chat_history) > 11:
        chat_history = [chat_history[0]] + chat_history[-10:]

    try:
        # 6. ENVIAR TODA LA MEMORIA AL CEREBRO
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_history,
            max_tokens=150,
            temperature=0.8 
        )
        
        respuesta_texto = r.choices[0].message.content
        
        # 7. GUARDAR LA RESPUESTA DE TARS EN LA MEMORIA
        chat_history.append({"role": "assistant", "content": respuesta_texto})
        
        return respuesta_texto
        
    except Exception as e: 
        return f"Error en el cerebro de TARS: {e}"
