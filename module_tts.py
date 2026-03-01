#!/usr/bin/env python3
import os
import subprocess
import aiohttp
import asyncio
from modules.module_config import load_config
import modules.tars_status as status 

CONFIG = load_config()

# === TUS DATOS DE ELEVENLABS ===
ELEVENLABS_API_KEY = "sk_820f5d255c84e9a86df0b87b339a51b7b14f9405414ad158"
ELEVENLABS_VOICE_ID = "NDeNvFOosDh4L0JoDYIq" 
# ===============================

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "tu_api_key_aqui":
        print("❌ TTS ERROR: Falta configurar la API Key de ElevenLabs.")
        return

    try:
        # 1. SEMÁFORO ROJO: Apagamos el oído
        status.is_speaking = True 
        print(f"⚡ Conectando a ElevenLabs (Modo Ultra-Rápido)...")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "output_format": "mp3_44100_128",
            "optimize_streaming_latency": 3 # ¡Esto es lo que quita el retraso!
        }

        # Lanzamos el reproductor mpg123 preparado para recibir el audio
        cmd = ["mpg123", "-q", "-"]
        proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        # Descargamos e inyectamos el audio al altavoz a la vez
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    print(f"❌ ERROR ElevenLabs: {response.status}")
                    return
                
                print(f"🔊 TARS HABLANDO...")
                async for chunk in response.content.iter_chunked(4096):
                    if chunk:
                        proceso.stdin.write(chunk)

        proceso.stdin.close()
        proceso.wait()

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        
    finally:
        # 2. SEMÁFORO VERDE: Despertamos el oído
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): 
    pass
