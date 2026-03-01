#!/usr/bin/env python3
import os
import re
import asyncio
import random
import subprocess
from modules.module_config import load_config
from modules.module_messageQue import queue_message
from modules.module_llm import process_completion
from modules.module_tts import play_audio_chunks
import modules.tars_status as status 

CONFIG = load_config()

# === Configuración de Muletillas ===
FILLER_DIR = "/home/javiersg/TARS-AI/src/assets/fillers/"

# Variables Globales
ui_manager = None
stt_manager = None

def play_local_filler():
    """
    Reproduce un archivo de audio local de forma instantánea 
    usando un proceso independiente (Popen) para no bloquear el sistema.
    """
    try:
        if not os.path.exists(FILLER_DIR):
            return
            
        archivos = [f for f in os.listdir(FILLER_DIR) if f.endswith((".mp3", ".wav"))]
        if archivos:
            archivo = random.choice(archivos)
            ruta = os.path.join(FILLER_DIR, archivo)
            
            # Usamos mpg123 para MP3 o aplay para WAV. 
            # -q es modo quiet (sin logs innecesarios)
            if archivo.endswith(".mp3"):
                subprocess.Popen(["mpg123", "-q", ruta])
            else:
                subprocess.Popen(["aplay", "-q", ruta])
    except Exception as e:
        print(f"⚠️ Error al disparar muletilla local: {e}")

def initialize_managers(mem_mgr, char_mgr, stt_mgr, ui_mgr, shutdown_evt, batt_mod):
    global ui_manager, stt_manager
    ui_manager = ui_mgr
    stt_manager = stt_mgr
    queue_message("SYSTEM: Managers initialized (Solid Speech Mode).")

def wake_word_callback(wake_response="¿Sí?"):
    """Respuesta inmediata al detectar la palabra clave (TARS)"""
    if status.is_speaking: return
    
    if ui_manager:
        ui_manager.deactivate_screensaver()
        ui_manager.update_data("TARS", wake_response, "TARS")
    
    status.is_speaking = True
    try:
        asyncio.run(play_audio_chunks(wake_response, "openai", True))
    finally:
        status.is_speaking = False

def utterance_callback(message):
    """
    Lógica principal: Muletilla local -> Procesado completo -> Respuesta sólida.
    """
    if not message or status.is_speaking:
        return

    user_text = str(message)
    if ui_manager:
        ui_manager.update_data("USER", user_text, "USER")
    
    queue_message(f"USER: {user_text}")

    # 1. COMANDO DE APAGADO (Prioridad)
    cmd = user_text.lower()
    if "apágate" in cmd and "tars" in cmd:
        asyncio.run(play_audio_chunks("Secuencia de apagado. Hasta la próxima, piloto.", "openai"))
        os.system("sudo shutdown -h now")
        return

    # 2. DISPARAR MULETILLA LOCAL (Latencia 0)
    # Esto suena inmediatamente mientras el cerebro empieza a trabajar
    play_local_filler()

    try:
        status.is_speaking = True
        
        # 3. GENERAR RESPUESTA COMPLETA
        # Obtenemos el generador y lo vaciamos en una lista para tener el bloque de texto
        respuesta_gen = process_completion(user_text)
        full_reply = "".join(list(respuesta_gen))
        
        # Limpieza de etiquetas de pensamiento o basura visual
        full_reply = re.sub(r"<think>.*?</think>", "", full_reply, flags=re.DOTALL).strip()

        # 4. MOSTRAR EN PANTALLA Y HABLAR (Bloque sólido)
        if ui_manager:
            ui_manager.update_data("TARS", full_reply, "TARS")
        
        # Enviamos el párrafo entero para que la entonación sea perfecta
        asyncio.run(play_audio_chunks(full_reply, "openai"))

    except Exception as e:
        queue_message(f"Error procesando flujo: {e}")
        print(f"❌ Error: {e}")
    finally:
        # Liberamos el micrófono para la siguiente frase
        status.is_speaking = False

def post_utterance_callback():
    """Función para evitar errores de importación en app.py"""
    pass
