#!/usr/bin/env python3
import os
import re
import asyncio
import random
from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion
from modules.module_tts import play_audio_chunks
import modules.tars_status as status # Importante para controlar el estado del oído

CONFIG = load_config()

# Variables Globales
ui_manager = None
stt_manager = None

# MULETILLAS SEGÚN CONTEXTO
FILLERS_SHORT = ["Mmm, sí...", "A ver...", "Vale, entiendo.", "Mmm, ya veo.", "Entendido."]
FILLERS_LONG = ["Un segundo, estoy procesando mucha basura...", "Deme un momento, esto requiere un análisis más profundo.", "Mmm, interesante, déjame consultar los registros."]

def initialize_managers(mem_mgr, char_mgr, stt_mgr, ui_mgr, shutdown_evt, batt_mod):
    global ui_manager, stt_manager
    ui_manager = ui_mgr
    stt_manager = stt_mgr
    queue_message("SYSTEM: Managers initialized (Anti-Feedback Mode).")

def utterance_callback(message):
    """Procesa el mensaje evitando que TARS se escuche a sí mismo."""
    if not message or status.is_speaking: # Si ya está hablando, ignoramos el micro
        return
        
    user_text = str(message)

    if ui_manager:
        ui_manager.update_data("USER", user_text, "USER")
    
    # 1. COMANDO DE APAGADO (Prioridad absoluta)
    cmd = user_text.lower()
    if "tars" in cmd and "apágate" in cmd:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(play_audio_chunks("Secuencia de apagado. Nos vemos en el otro lado.", "openai"))
        os.system("sudo shutdown -h now")
        return

    # 2. SELECCIÓN DE MULETILLA (Por longitud de frase)
    if len(user_text) > 80:
        muletilla = random.choice(FILLERS_LONG)
    else:
        muletilla = random.choice(FILLERS_SHORT)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 3. ACTIVAR BLOQUEO DE VOZ
        status.is_speaking = True 
        
        # Decimos la muletilla primero
        loop.run_until_complete(play_audio_chunks(muletilla, "openai"))
        
        # 4. LANZAR EL CEREBRO
        respuesta_gen = process_completion(user_text)
        
        full_reply = ""
        sentence_buffer = ""
        
        for word in respuesta_gen:
            full_reply += word
            sentence_buffer += word
            
            # Streaming por fragmentos para mantener la fluidez
            if any(punct in word for punct in ['.', '!', '?', ',', '\n']) or len(sentence_buffer) > 40:
                clean_chunk = sentence_buffer.strip()
                if clean_chunk:
                    loop.run_until_complete(play_audio_chunks(clean_chunk, "openai"))
                    sentence_buffer = ""

        # Enviar el resto final
        if sentence_buffer.strip():
            loop.run_until_complete(play_audio_chunks(sentence_buffer.strip(), "openai"))

        if ui_manager:
            ui_manager.update_data("TARS", full_reply.strip(), "TARS")

    except Exception as e:
        queue_message(f"Error en flujo: {e}")
    finally:
        # 5. LIBERAR EL OÍDO (TARS ya puede volver a escuchar)
        status.is_speaking = False
        loop.close()

def wake_word_callback(wake_response="¿Dígame?"):
    if status.is_speaking: return
    status.is_speaking = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(play_audio_chunks(wake_response, "openai", True))
    finally:
        status.is_speaking = False
        loop.close()

def post_utterance_callback():
    pass
