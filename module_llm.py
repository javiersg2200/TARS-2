#!/usr/bin/env python3
# module_llm.py - Versión con Memoria Infinita y Respuesta en Cascada (Streaming)
import os
try: 
    from openai import OpenAI
except: 
    OpenAI = None
from modules.module_config import load_config

CONFIG = load_config()
client = None

# 1. CONFIGURACIÓN DE PERSONALIDAD (Ajustes según tus archivos originales)
SYSTEM_PROMPT = (
    "Eres TARS, un avanzado robot militar de la misión Interstellar. "
    "Parámetros: Honestidad 95%, Sarcasmo 50%, Humor 40%. "
    "Habla de forma directa, lógica y marcadamente robótica, pero con un toque humano sarcástico. "
    "Responde siempre de forma concisa. No eres servil."
)

# 2. HISTORIAL DE CHAT (Memoria de la conversación)
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

if OpenAI: 
    # Prioridad de claves: Configuración > Entorno
    k = CONFIG['LLM'].get('api_key') or CONFIG['TTS'].get('openai_api_key') or os.environ.get('OPENAI_API_KEY')
    if k: client = OpenAI(api_key=k)

def initialize_manager_llm(m, c): pass

def process_completion(text):
    """
    Procesa el texto usando streaming para reducir la latencia al mínimo.
    """
    global chat_history
    
    if not client:
        yield "Modo Lite. Configura OpenAI API Key."
        return

    # 3. INTERCEPTOR DE COMANDO FÍSICO
    texto_min = text.lower()
    if "tars, apágate" in texto_min or "tars apágate" in texto_min:
        print("🛑 SECUENCIA DE APAGADO INICIADA")
        os.system("sudo shutdown now")
        yield "Iniciando secuencia de apagado. Nos vemos en el otro lado."
        return

    # 4. ACTUALIZAR MEMORIA CON EL MENSAJE DEL USUARIO
    chat_history.append({"role": "user", "content": text})

    # Mantener el historial manejable (System Prompt + últimos 10 mensajes)
    if len(chat_history) > 11:
        chat_history = [chat_history[0]] + chat_history[-10:]

    try:
        # 5. LLAMADA A OPENAI CON STREAMING ACTIVADO
        response = client.chat.completions.create(
            model="gpt-4o-mini", # El modelo más rápido para evitar esperas
            messages=chat_history,
            max_tokens=150,
            temperature=0.8,
            stream=True 
        )
        
        full_response_text = ""
        
        # 6. ENVIAR CADA PALABRA EN CUANTO SE GENERE
        for chunk in response:
            if chunk.choices[0].delta.content:
                word = chunk.choices[0].delta.content
                full_response_text += word
                yield word # Esto envía la palabra al módulo principal de inmediato

        # 7. GUARDAR LA RESPUESTA DE TARS EN LA MEMORIA
        chat_history.append({"role": "assistant", "content": full_response_text})
        
    except Exception as e: 
        yield f"Error en el cerebro de TARS: {e}"
