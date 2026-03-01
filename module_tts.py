#!/usr/bin/env python3
import os
import subprocess
from openai import OpenAI
from modules.module_config import load_config
import modules.tars_status as status 

CONFIG = load_config()

def get_openai_client():
    # Coge la API Key de OpenAI que ya tienes configurada para el cerebro
    k = CONFIG['TTS'].get('openai_api_key') or CONFIG['LLM'].get('api_key') or os.environ.get("OPENAI_API_KEY")
    if k: return OpenAI(api_key=k)
    return None

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    client = get_openai_client()
    
    if not client:
        print("❌ TTS ERROR: Falta configurar la API Key de OpenAI.")
        return

    try:
        # 1. SEMÁFORO ROJO: Apagamos el oído
        status.is_speaking = True 
        print(f"⚡ Conectando a OpenAI TTS (Modo Streaming Ultra-Rápido)...")

        # 2. Pedimos el audio a OpenAI
        response = client.audio.speech.create(
            model="tts-1", # tts-1 está optimizado para velocidad y latencia baja
            voice="onyx",  # Onyx es una voz muy grave y profunda
            input=text,
            response_format="mp3"
        )

        print(f"🔊 TARS HABLANDO...")
        
        # 3. Magia Negra de Linux: 
        # Reproducimos el MP3 al vuelo (-q), forzando 44100Hz (-r 44100) y estéreo (-2)
        # Esto evita crashes de ALSA y no escribe NADA en la tarjeta SD (latencia cero).
        cmd = ["mpg123", "-q", "-r", "44100", "-2", "-"]
        proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # Inyectamos los trozos de audio al altavoz según nos van llegando de internet
        for chunk in response.iter_bytes(chunk_size=4096):
            if chunk:
                proceso.stdin.write(chunk)

        proceso.stdin.close()
        proceso.wait()

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        
    finally:
        # 4. SEMÁFORO VERDE: Despertamos el oído
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): 
    pass
