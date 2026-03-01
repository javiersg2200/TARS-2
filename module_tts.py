#!/usr/bin/env python3
import os
import subprocess
import asyncio
from modules.module_config import load_config
import modules.tars_status as status 

# Rutas absolutas a los archivos de voz de TARS
MODEL_PATH = "/home/javiersg/TARS-AI/src/character/TARS/voice/TARS.onnx"
CONFIG_PATH = "/home/javiersg/TARS-AI/src/character/TARS/voice/TARS.onnx.json"

def limpiar_texto_para_piper(texto):
    # Piper en inglés crashea con caracteres españoles. Los eliminamos.
    return texto.replace("¿", "").replace("¡", "")

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    
    if not os.path.exists(MODEL_PATH) or not os.path.exists(CONFIG_PATH):
        print(f"❌ TTS ERROR: No encuentro los archivos de voz en /home/javiersg/TARS-AI/src/character/TARS/voice/")
        return

    try:
        # 1. SEMÁFORO ROJO: Apagamos el oído
        status.is_speaking = True 
        print(f"⚙️ Generando voz de TARS en local (Piper)...")

        texto_limpio = limpiar_texto_para_piper(text)

        # 2. Generar audio con Piper (Usamos python3 -m para evitar errores de PATH)
        piper_cmd = [
            "python3", "-m", "piper", 
            "--model", MODEL_PATH, 
            "--config", CONFIG_PATH, 
            "--output_file", "raw_speech.wav"
        ]
        
        proceso = subprocess.run(
            piper_cmd, 
            input=texto_limpio.encode('utf-8'), 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.PIPE # Capturamos el error real si falla
        )

        if proceso.returncode != 0:
            error_msg = proceso.stderr.decode('utf-8')
            print(f"❌ ERROR PIPER EXACTO: {error_msg}")
            return

        # 3. CONVERSIÓN CRÍTICA: Forzamos 44100Hz y 2 Canales
        subprocess.run(
            "ffmpeg -y -i raw_speech.wav -ar 44100 -ac 2 ready_speech.wav -loglevel quiet", 
            shell=True
        )

        # 4. Reproducir
        print(f"🔊 TARS HABLANDO...")
        subprocess.run("aplay -D default ready_speech.wav -q", shell=True)

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        await asyncio.sleep(1) 
        
    finally:
        # 5. SEMÁFORO VERDE: Despertamos el oído
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): 
    pass
