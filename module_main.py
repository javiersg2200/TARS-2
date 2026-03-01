#!/usr/bin/env python3
import os
import re
import asyncio
import random
from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion
from modules.module_tts import play_audio_chunks

CONFIG = load_config()

# Variables Globales (inicializadas por app.py)
ui_manager = None
character_manager = None
memory_manager = None
stt_manager = None
shutdown_event = None
battery_module = None

# MULETILLAS NATURALES (Marcadores de conversación humana)
TARS_FILLERS = [
    "Mmm, sí...",
    "A ver...",
    "Vale, entiendo.",
    "Mmm, ya veo...",
    "Bueno, déjame mirar.",
    "Entiendo...",
    "Mmm, interesante.",
    "Vale..."
]

def initialize_managers(mem_mgr, char_mgr, stt_mgr, ui_mgr, shutdown_evt, batt_mod):
    global memory_manager, character_manager, stt_manager, ui_manager, shutdown_event, battery_module
    memory_manager = mem_mgr
    character_manager = char_mgr
    stt_manager = stt_mgr
    ui_manager = ui_mgr
    shutdown_event = shutdown_evt
    battery_module = batt_mod
    queue_message("SYSTEM: Managers initialized (Natural Mode).")

def wake_word_callback(wake_response="¿Sí?"):
    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("TARS", wake_response, "TARS")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(play_audio_chunks(wake_response, "openai", True))
    finally:
        loop.close()

def utterance_callback(message):
    """Procesa el mensaje con un 'puente' conversacional humano."""
    if not message: return
    user_text = str(message)

    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("USER", user_text, "USER")
    
    queue_message(f"USER: {user_text}")

    # Interceptor de Apagado (Por si quieres mandarlo a dormir)
    cmd = user_text.lower()
    if "apágate" in cmd and "tars" in cmd:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(play_audio_chunks("Entendido. Apagando sistemas.", "openai"))
        os.system("sudo shutdown -h now")
        return

    # --- EL TRUCO DE LA NATURALIDAD ---
    # 1. Elegimos la muletilla humana
    muletilla = random.choice(TARS_FILLERS)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 2. La decimos INMEDIATAMENTE
        # Como es una frase muy corta, el TTS la genera en milisegundos.
        loop.run_until_complete(play_audio_chunks(muletilla, "openai"))
        
        # 3. Mientras el usuario escucha la muletilla, arrancamos el cerebro
        respuesta_gen = process_completion(user_text)
        
        full_reply = ""
        sentence_buffer = ""
        
        for word in respuesta_gen:
            full_reply += word
            sentence_buffer += word
            
            # Streaming por fragmentos para no perder el ritmo
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
        loop.close()

def post_utterance_callback():
    pass
