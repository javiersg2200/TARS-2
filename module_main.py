#!/usr/bin/env python3
import os
import threading
import json
import re
import time
import asyncio
from modules.module_config import load_config
from modules.module_messageQue import queue_message

# Importamos versiones seguras
try:
    from modules.module_llm import process_completion
except ImportError:
    def process_completion(x): yield "Error: LLM no encontrado"

try:
    from modules.module_tts import play_audio_chunks
except ImportError:
    async def play_audio_chunks(*args, **kwargs): pass

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
    queue_message("SYSTEM: Managers initialized (Safe Mode).")

def wake_word_callback(wake_response="¿Sí?"):
    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("TARS", wake_response, "TARS")
    
    try:
        asyncio.run(play_audio_chunks(wake_response, "openai", True))
    except Exception as e:
        print(f"Audio Error: {e}")

def utterance_callback(message):
    """Procesa el mensaje del usuario con soporte para Streaming."""
    if not message: return

    # 1. Extraer texto limpio
    user_text = message if isinstance(message, str) else str(message)
    if not user_text: return

    # 2. Actualizar UI
    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("USER", user_text, "USER")
    
    queue_message(f"USER: {user_text}")

    # 3. Comandos de Sistema (Duplicado aquí por seguridad, aunque el LLM también lo gestiona)
    cmd = user_text.lower()
    if "apágate" in cmd and "tars" in cmd:
        if ui_manager: ui_manager.update_data("SYSTEM", "Apagando...", "SYSTEM")
        os.system("sudo shutdown -h now")
        return

    # 4. Generar Respuesta (LLM con Streaming)
    if ui_manager: ui_manager.update_data("TARS", "Pensando...", "TARS")
    
    try:
        # Ahora process_completion es un generador (yield)
        respuesta_gen = process_completion(user_text)
        
        full_reply = ""
        
        # Consumimos el generador para obtener el texto completo
        # NOTA: En versiones futuras podemos enviar 'chunks' a la voz para más velocidad
        for word in respuesta_gen:
            full_reply += word
            # Opcional: imprimir palabras en tiempo real en la terminal
            # print(word, end="", flush=True)

        # Limpieza de etiquetas de pensamiento (si usas modelos tipo DeepSeek)
        full_reply = re.sub(r"<think>.*?</think>", "", full_reply, flags=re.DOTALL).strip()
        
        # 5. Mostrar y Hablar (Ejecución de la voz)
        if ui_manager: ui_manager.update_data("TARS", full_reply, "TARS")
        
        # Usamos un loop de asyncio limpio para la Raspberry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(play_audio_chunks(full_reply, "openai"))
        finally:
            loop.close()
        
    except Exception as e:
        queue_message(f"Error procesando respuesta: {e}")
        print(f"DEBUG ERROR: {e}")

def post_utterance_callback():
    pass
