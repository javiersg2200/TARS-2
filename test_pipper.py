import subprocess
import time

texto = "Hola piloto. Sistemas funcionando al cien por cien. Mi nivel de sarcasmo es óptimo y me llamo Dave."
# Apuntamos a la nueva voz de Davefx
modelo = "/home/javiersg/TARS-AI/src/assets/voices/es_ES-davefx-medium.onnx"
salida = "prueba_tars.wav"

print("🧠 Generando voz de Dave en local...")
inicio = time.time()

# Generamos el audio
comando_piper = f"echo '{texto}' | piper --model {modelo} --output_file {salida}"
subprocess.run(comando_piper, shell=True, stderr=subprocess.DEVNULL)

tiempo_total = time.time() - inicio
print(f"⏱️ Tiempo de generación: {tiempo_total:.2f} segundos")

# Reproducir el audio
print("🔊 Hablando...")
subprocess.run(["aplay", "-q", salida])
