#!/usr/bin/env python3
import os
import subprocess
import asyncio
from openai import OpenAI
from modules.module_config import load_config
import modules.tars_status as status 

CONFIG = load_config()

def get_openai_client():
    # Intentamos sacar la clave de la configuración
    tts_conf = CONFIG['TTS']
    api_key = getattr(tts_conf, 'openai_api_key', None) or getattr(CONFIG['LLM'], 'api_key', None)
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    return OpenAI(api_key=api_key) if api_key else None

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    client = get_openai_client()
    
    if not client:
        print("❌ TTS ERROR: No hay API Key de OpenAI.")
        return

    try:
        status.is_speaking = True 
        print(f"⚡ Voz Onyx (OpenAI) en streaming...")

        # Pedimos el audio a OpenAI (onyx es la voz más TARS que tienen)
        response = client.audio.speech.create(
            model="tts-1", # El modelo más rápido
            voice="onyx", 
            input=text,
            response_format="mp3"
        )

        # Reproductor mpg123 configurado para mínima latencia
        cmd = ["mpg123", "-q", "-r", "44100", "--stereo", "-"]
        proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        print(f"🔊 TARS HABLANDO...")
        for chunk in response.iter_bytes(chunk_size=1024):
            if chunk:
                proceso.stdin.write(chunk)

        proceso.stdin.close()
        proceso.wait()

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        await asyncio.sleep(0.5)
        
    finally:
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): pass
