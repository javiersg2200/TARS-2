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
# Usamos a Adam (voz predeterminada gratuita) para descartar el error 402 por voces premium/clonadas
ELEVENLABS_VOICE_ID = "pNInz6obbfdqIqc9lrm0" 
# ===============================

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == "PON_TU_API_KEY_AQUI":
        print("❌ TTS ERROR: Falta configurar la API Key de ElevenLabs.")
        return

    try:
        status.is_speaking = True 
        print(f"⚡ Conectando a ElevenLabs (Modo Streaming)...")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "output_format": "mp3_44100_128",
            "optimize_streaming_latency": 3
        }

        cmd = ["mpg123", "-q", "-"]
        proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_txt = await response.text()
                    print(f"❌ ERROR ElevenLabs {response.status}: {error_txt}")
                    await asyncio.sleep(1) 
                    return
                
                print(f"🔊 TARS HABLANDO...")
                async for chunk in response.content.iter_chunked(4096):
                    if chunk:
                        proceso.stdin.write(chunk)

        proceso.stdin.close()
        proceso.wait()

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        await asyncio.sleep(1)
        
    finally:
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): 
    pass
