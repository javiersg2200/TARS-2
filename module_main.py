#!/usr/bin/env python3
import os
import re
import asyncio
from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion
from modules.module_tts import play_audio_chunks

CONFIG = load_config()

# Variables Globales
ui_manager = None
character_manager = None
memory_manager = None
stt_manager = None
shutdown_event = None
battery_module = None

def initialize_managers(mem_mgr, char_mgr, stt_mgr, ui_mgr, shutdown_evt, batt_mod):
    global memory_manager, character_manager, stt_manager, ui_manager, shutdown_event, battery_module
    memory_manager = mem_mgr
    character_manager = char_mgr
    stt_manager = stt_mgr
    ui_manager = ui_mgr
    shutdown_event = shutdown_evt
    battery_module = batt_mod
    queue_message("SYSTEM: Managers initialized (Turbo Mode).")

def wake_word_callback(wake_response="¿Dígame?"):
    """Respuesta inmediata al detectar la palabra clave"""
    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("TARS", wake_response, "TARS")
    
    # Ejecución asíncrona segura para la Raspberry
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(play_audio_chunks(wake_response, "openai", True))
    finally:
        loop.close()

def utterance_callback(message):
    """Procesa el mensaje del usuario con fragmentación para latencia mínima."""
    if not message: return
    user_text = str(message)

    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("USER", user_text, "USER")
    
    queue_message(f"USER: {user_text}")

    # 1. Comandos de Sistema Críticos
    cmd = user_text.lower()
    if "apágate" in cmd and "tars" in cmd:
        if ui_manager: ui_manager.update_data("SYSTEM", "Cerrando sistemas...", "SYSTEM")
        os.system("sudo shutdown -h now")
        return

    # 2. Generador del Cerebro (Streaming)
    respuesta_gen = process_completion(user_text)
    
    full_reply = ""
    sentence_buffer = ""
    
    # Loop de audio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        for word in respuesta_gen:
            full_reply += word
            sentence_buffer += word
            
            # Disparamos el audio si hay un signo de puntuación o el buffer es razonable
            if any(punct in word for punct in ['.', '!', '?', ',', '\n']) or len(sentence_buffer) > 45:
                clean_chunk = sentence_buffer.strip()
                if clean_chunk:
                    loop.run_until_complete(play_audio_chunks(clean_chunk, "openai"))
                    sentence_buffer = ""

        # Enviar el resto final si queda algo
        if sentence_buffer.strip():
            loop.run_until_complete(play_audio_chunks(sentence_buffer.strip(), "openai"))

        if ui_manager:
            ui_manager.update_data("TARS", full_reply.strip(), "TARS")

    except Exception as e:
        queue_message(f"Error en flujo TARS: {e}")
    finally:
        loop.close()

def post_utterance_callback():
    """Función requerida por app.py para procesos posteriores a la respuesta."""
    pass
