#!/usr/bin/env python3
import os
import subprocess
import asyncio
from openai import OpenAI
from modules.module_config import load_config
import modules.tars_status as status 

CONFIG = load_config()

def get_openai_client():
    # Usamos getattr() porque CONFIG['TTS'] es un objeto, no un diccionario
    tts_conf = CONFIG['TTS']
    api_key = getattr(tts_conf, 'openai_api_key', None)
    
    # Si no la encuentra ahí, probamos en la sección del Cerebro (LLM)
    if not api_key:
        try:
            llm_conf = CONFIG['LLM']
            api_key = getattr(llm_conf, 'api_key', None)
        except:
            pass
            
    # Último intento: Variables de entorno del sistema
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    if api_key:
        return OpenAI(api_key=api_key)
        
    return None

async def play_audio_chunks(text, tts_option=None, is_wakeword=False):
    if not text: return
    client = get_openai_client()
    
    if not client:
        print("❌ TTS ERROR: No encuentro la API Key de OpenAI.")
        return

    try:
        # 1. SEMÁFORO ROJO: Apagamos el oído
        status.is_speaking = True 
        print(f"⚡ Conectando a OpenAI TTS (Modo Streaming)...")

        # 2. Pedimos el audio a OpenAI
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            response_format="mp3"
        )

        print(f"🔊 TARS HABLANDO...")
        
        # 3. Magia Negra de Linux para reproducir al vuelo sin latencia
        cmd = ["mpg123", "-q", "-r", "44100", "-2", "-"]
        proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE)

        for chunk in response.iter_bytes(chunk_size=4096):
            if chunk:
                proceso.stdin.write(chunk)

        proceso.stdin.close()
        proceso.wait()

    except Exception as e:
        print(f"❌ TTS ERROR: {e}")
        await asyncio.sleep(1) 
        
    finally:
        # 4. SEMÁFORO VERDE: Despertamos el oído
        print("✅ Fin de frase.")
        status.is_speaking = False

def update_tts_settings(*args, **kwargs): 
    pass
