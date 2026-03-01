#!/usr/bin/env python3
import os
import re
import asyncio
from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion
from modules.module_tts import play_audio_chunks

CONFIG = load_config()

# Variables Globales (se asumen inicializadas por app.py)
ui_manager = None

def initialize_managers(mem_mgr, char_mgr, stt_mgr, ui_mgr, shutdown_evt, batt_mod):
    global ui_manager
    ui_manager = ui_mgr
    queue_message("SYSTEM: Managers initialized (Turbo Mode).")

def utterance_callback(message):
    if not message: return
    user_text = str(message)

    if ui_manager:
        ui_manager.update_data("USER", user_text, "USER")
    
    # 1. GENERADOR DEL CEREBRO
    # Empezamos a recibir palabras una a una
    respuesta_gen = process_completion(user_text)
    
    full_reply = ""
    sentence_buffer = ""
    
    print("TARS pensando y hablando...")

    # Creamos un bucle para manejar el audio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        for word in respuesta_gen:
            full_reply += word
            sentence_buffer += word
            
            # 2. ¿CUÁNDO EMPEZAR A LEER? 
            # Si detectamos un final de frase (. ! ?) o la frase ya es larga (20 caracteres), disparar audio
            if any(punct in word for punct in ['.', '!', '?', ',', '\n']) or len(sentence_buffer) > 40:
                clean_chunk = sentence_buffer.strip()
                if clean_chunk:
                    # ENVIAMOS EL TROZO A LA BOCA SIN ESPERAR AL FINAL
                    loop.run_until_complete(play_audio_chunks(clean_chunk, "openai"))
                    sentence_buffer = "" # Vaciamos para el siguiente trozo

        # 3. ENVIAR EL RESTO (si quedó algo sin puntos al final)
        if sentence_buffer.strip():
            loop.run_until_complete(play_audio_chunks(sentence_buffer.strip(), "openai"))

        # Actualizar UI al final con todo el texto acumulado
        if ui_manager:
            ui_manager.update_data("TARS", full_reply.strip(), "TARS")

    finally:
        loop.close()

def wake_word_callback(wake_response="¿Dígame?"):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(play_audio_chunks(wake_response, "openai", True))
    loop.close()
