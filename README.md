# Control Conversacional de Drones con IA

Este proyecto se ha desarrollado como una contribución al proyecto colaborativo **Drone Engineering Ecosystem (DEE)**. El objetivo principal ha sido incorporar capacidades de inteligencia artificial para la interpretación de comandos y una interacción conversacional natural.

## Principales funcionalidades

* **Control de dron por voz**: despegue, aterrizaje, movimientos y más, todo mediante comandos en lenguaje natural.
* **Modo conversacional con personalidades**: distintos estilos de interacción (Normal, Gracioso, Borde, Preguntón), que ofrecen respuestas adaptadas al contexto.
* **Planificación de misiones**: se pueden dictar rutas o patrones de vuelo (p. ej., "dibuja un cuadrado de 5 metros de lado"), con previsualización en un mapa.
* **Modo manual**: panel de control tradicional para maniobras finas o de emergencia, complementando la interacción por voz.
* **Visualización en tiempo real**: se muestra la posición del dron y su estado en una interfaz web, permitiendo un seguimiento continuo de la misión.

## Demo

Para comprender el funcionamiento de esta aplicación, puedes consultar el siguiente **video**: https://youtu.be/ArKzQa9z8J8

En el video se emplea el simulador MAVLink (Mission Planner)  para enseñar cómo el sistema recibe y ejecuta órdenes por voz, así como la planificación de rutas y el cambio a modo manual.

También se incluye un segundo **video con una explicación detallada del código**: https://youtu.be/ZkojRP_BITg

En él se describe la organización de los módulos (procesamiento de audio, lógica de IA, interfaz web, etc.) y se brindan pautas para ampliar o personalizar el proyecto.

## Instalación

### Prerequisitos

1. **Python 3.8+** y un broker MQTT (Mosquitto)
2. **FFmpeg** instalado en el sistema (para conversión de audio) https://github.com/GyanD/codexffmpeg/releases/tag/7.1
3. **Certificados SSL** generados con OpenSSL
4. **Modelo Vosk** en español (p. ej. [vosk-model-small-es-0.42](https://alphacephei.com/vosk/models))
### Configuración rápida

1. Clonar el repositorio:
```bash
git clone https://github.com/tuUsuario/tuRepositorio.git
cd tuRepositorio
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar MQTT:
```bash
# mosquitto1884.conf
listener 1884
allow_anonymous true

# Iniciar broker:
mosquitto -c mosquitto1884.conf
```

4. Generar certificados SSL:
```bash
mkdir openssl
cd openssl
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

5. Descargar e instalar el modelo de Vosk (en español), colocando los archivos en la carpeta que usarás en el código.
   
  En `routes.py` actualizar la línea:
   
```python
voice_recognition = VoiceRecognitionSystem(r"ruta\al\modelo\vosk-model-small-es-0.42")
   ```

6. Colocar ffmpeg.exe en la carpeta bin/, o bien asegurarse de que esté instalado y disponible en la variable de entorno del sistema.
   
7. Cambiar la clave api
   
  En `voice_control.py` actualizar la línea:
  ```python
openai.api_key = "API_key"
   ```
La API key tiene que ser solicitada al profesor

8. Ejecutar:
```bash
python run.py
```

## Configuración y personalización

El sistema puede personalizarse editando los siguientes aspectos:

1. **Prompts de IA**: Ajustar respuestas y comportamientos en `voice_control.py`
2. **Personalidades**: Añadir nuevos modos en el sistema de interacción

