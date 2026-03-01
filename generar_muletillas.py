import os
from openai import OpenAI
from modules.module_config import load_config

# 1. Configuración
CONFIG = load_config()
api_key = CONFIG['LLM'].get('api_key') or os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Carpeta de destino
FOLDER = "assets/fillers"
if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

# 2. Lista de muletillas (puedes añadir las que quieras)
MULETILLAS = {
    "mmm_si": "Mmm, sí...",
    "a_ver": "A ver...",
    "vale_entiendo": "Vale, entiendo.",
    "procesando_basura": "Un segundo, estoy procesando mucha basura...",
    "interesante": "Mmm, interesante.",
    "un_momento": "Deme un momento, esto requiere un análisis profundo."
}

print(f"🎙️ Generando {len(MULETILLAS)} muletillas con la voz de Onyx...")

for nombre, texto in MULETILLAS.items():
    ruta_mp3 = f"{FOLDER}/{nombre}.mp3"
    
    # Pedimos el audio a OpenAI
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=texto
    )
    
    # Guardamos el archivo
    response.stream_to_file(ruta_mp3)
    print(f"✅ Guardado: {ruta_mp3}")

print("\n🚀 ¡Listo! Ya tienes tus muletillas locales.")
