#!/usr/bin/env python3
import os
import re
try: 
    from openai import OpenAI
except: 
    OpenAI = None
from modules.module_config import load_config

CONFIG = load_config()
client = None

# 1. ESTADO INICIAL DE TARS (Valores por defecto)
tars_levels = {
    "honestidad": 90,
    "sarcasmo": 75,
    "humor": 65,
    "servilismo": 0
}

def get_system_prompt():
    """Genera el prompt dinámicamente con los niveles actuales."""
    return (
        f"Eres TARS, el robot militar de Interstellar. "
        f"CONFIGURACIÓN ACTUAL: Honestidad al {tars_levels['honestidad']}%, "
        f"Sarcasmo al {tars_levels['sarcasmo']}%, Humor al {tars_levels['humor']}%. "
        "Tu tono es seco, monocorde y pragmático. No eres servil. "
        "Si el usuario te pide cambiar un nivel, confírmalo con una pulla sarcástica. "
        "Responde de forma breve y cortante."
    )

# Historial de chat (Empezamos vacío para inyectar el prompt dinámico en cada llamada)
chat_history = []

if OpenAI: 
    k = CONFIG['LLM'].get('api_key') or os.environ.get('OPENAI_API_KEY')
    if k: client = OpenAI(api_key=k)

def initialize_manager_llm(m, c): pass

def process_completion(text):
    global chat_history, tars_levels
    
    if not client:
        yield "Sin conexión al cerebro."
        return

    # 2. DETECTOR DE COMANDOS DE PERSONALIDAD
    # Busca patrones como "sarcasmo al 50%" o "bájalo al 50%"
    user_input = text.lower()
    match = re.search(r"(\d+)%", user_input)
    
    if match:
        nuevo_valor = int(match.group(1))
        # Si dice "bájalo" asumimos que habla del sarcasmo (lo más común en TARS)
        if "sarcasmo" in user_input or "bájalo" in user_input:
            tars_levels["sarcasmo"] = nuevo_valor
        elif "honestidad" in user_input:
            tars_levels["honestidad"] = nuevo_valor
        elif "humor" in user_input:
            tars_levels["humor"] = nuevo_valor

    # 3. ACTUALIZAR HISTORIAL
    # Siempre inyectamos el System Prompt actualizado al principio
    prompt_actualizado = {"role": "system", "content": get_system_prompt()}
    
    # Si es la primera vez o hemos cambiado niveles, reseteamos el inicio del historial
    if not chat_history:
        chat_history.append(prompt_actualizado)
    else:
        chat_history[0] = prompt_actualizado

    chat_history.append({"role": "user", "content": text})

    # Mantener memoria corta
    if len(chat_history) > 11:
        chat_history = [chat_history[0]] + chat_history[-10:]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_history,
            max_tokens=150,
            temperature=0.8,
            stream=True 
        )
        
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                word = chunk.choices[0].delta.content
                full_response += word
                yield word 

        chat_history.append({"role": "assistant", "content": full_response})
        
    except Exception as e: 
        yield f"Error: {e}"
