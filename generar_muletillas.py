import os
from openai import OpenAI
from modules.module_config import load_config

CONFIG = load_config()
# Sacamos la key de donde esté guardada
api_key = getattr(CONFIG.get('LLM', {}), 'api_key', None) or os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

FOLDER = "/home/javiersg/TARS-AI/src/assets/fillers"
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

MULETILLAS = {
    "mmm_si": "Mmm, sí.",
    "a_ver": "A ver.",
    "vale": "Vale, entiendo.",
    "interesante": "Mmm, interesante."
}

print("🎙️ Generando muletillas con Onyx...")
for nombre, texto in MULETILLAS.items():
    ruta = f"{FOLDER}/{nombre}.mp3"
    response = client.audio.speech.create(model="tts-1", voice="onyx", input=texto)
    response.stream_to_file(ruta)
    print(f"✅ Creado: {ruta}")
