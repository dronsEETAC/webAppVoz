from flask import Blueprint, render_template, jsonify, request, send_from_directory
from app.voice_control import enviar_comando_openai, VoiceRecognitionSystem, PERSONALIDADES
from app.VoiceControlService import VoiceControlService
from app.plan_de_vuelo import crear_mision
from dronLink.Dron import Dron
from app.ModoGlobal import publish_command
from gtts import gTTS
from io import BytesIO
from flask_socketio import SocketIO
from app import socketio

import base64
import openai
import json
import os
import mimetypes
global recording
global video_writer
global filepath
global taking_photo
global expected_height
global expected_width
import cv2
import numpy as np
from datetime import datetime
dron = Dron()
main = Blueprint('main', __name__)

voice_control_service = VoiceControlService()
conectado=False
armado=False
recording = False
video_writer = None
taking_photo = False
voice_recognition = VoiceRecognitionSystem("C:/Users/Mariina/Desktop/Repositorio/WebAppHTTP/vosk-model-small-es-0.42")


@main.route('/static/js/<path:filename>')
def serve_js(filename):
    mimetypes.add_type('application/javascript', '.js')
    return send_from_directory('static/js', filename)


@main.route('/')
def index():
    return render_template('movil.html')
############################################################################################################

@main.route('/api/conectar_broker', methods=['POST'])
def conectar_broker():
    from app.ModoGlobal import mqtt_client_instance, connect_mqtt
    try:
        if mqtt_client_instance and mqtt_client_instance.is_connected():
            return jsonify({"message": "Broker ya conectado"}), 200

        client = connect_mqtt()
        if client and client.is_connected():
            return jsonify({"message": "Conexión al broker iniciada"}), 200
        else:
            return jsonify({"message": "Intentando conectar al broker..."}), 202

    except Exception as e:
        print(f"Error en conectar_broker: {e}")
        return jsonify({"error": "Error al conectar con el broker"}), 500



@main.route('/api/enviar_comandoMQTT', methods=['POST'])
def enviar_comandoMQTT():
    data = request.json
    comando = data.get('comando')
    if not comando:
        return jsonify({"error": "Comando inválido"}), 400

    try:
        if publish_command(comando):
            return jsonify({"message": f"Comando '{comando}' enviado"}), 200
        return jsonify({"error": "No hay conexión"}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error al enviar comando"}), 500

############################################################################################################

@main.route('/iniciar_captura', methods=['POST'])
def iniciar():
    voice_recognition.iniciar_captura()
    return jsonify({'message': 'Captura iniciada'})
@main.route('/detener_captura', methods=['POST'])
def detener():
    transcription = voice_recognition.detener_captura()
    if transcription:
        user_id = "usuario_demo"
        respuesta = enviar_comando_openai(user_id, transcription)
        return jsonify({
            'transcription': transcription,
            'respuesta': respuesta
        })
    return jsonify({
        'transcription': '',
        'respuesta': 'No se pudo procesar el audio'
    })
############################################################################################################

############################################################################################################

@main.route('/enviar_mensaje_predefinido', methods=['POST'])
def enviar_mensaje_predefinido():
    mensaje = "disminur la altura 4 metros"
    print(f"Mensaje predefinido enviado: {mensaje}")

    #enviar el mensaje
    respuesta = enviar_comando_openai(mensaje)

    #retorna mensaje y respuesta
    return jsonify({'message': mensaje, 'respuesta': respuesta})
@main.route('/enviar_comandoIA', methods=['POST'])
def enviar_comando():
    try:
        data = request.get_json()
        comando = data.get('comando', '').strip()

        print("\n=== INICIO PROCESAR COMANDO ===")
        print(f"Comando recibido: {comando}")
        print(f"Modo educativo: {voice_control_service.modo_educativo}")

        if not comando:
            return jsonify({
                "estado": "error",
                "message": "Por favor, proporciona un comando.",
                "audio_url": voice_control_service.text_to_speech("Por favor, proporciona un comando.")
            }), 400

        resultado = voice_control_service.procesar_comando_normal(comando)
        return jsonify(resultado)

    except Exception as e:
        print(f"Error en enviar_comandoIA: {e}")
        mensaje_error = "Ha ocurrido un error. Por favor, intenta de nuevo."
        return jsonify({
            "estado": "error",
            "message": mensaje_error,
            "audio_url": voice_control_service.text_to_speech(mensaje_error)
        }), 500

############################################################################################################

@main.route('/cambiar_personalidad', methods=['POST'])
def cambiar_personalidad():
    data = request.get_json()
    nueva_personalidad = data.get('personalidad', 'normal')
    user_id = "usuario_demo"

    if nueva_personalidad not in ["normal", "gracioso", "borde", "pregunton", "plan_vuelo", "preguntón"]:
        return jsonify({"error": "Personalidad no válida"}), 400

    voice_control_service.cambiar_personalidad(user_id, nueva_personalidad)
    return jsonify({"message": f"Personalidad cambiada a {nueva_personalidad}"}), 200


############################################################################################################
@main.route('/Plandevuelo')
def plan_de_vuelo():
    return render_template('plan_de_vuelo.html')

@main.route('/modalidades')  #no se usa por si acaso mas adelante
def modalidades():
    return render_template('modalidades.html')


@main.route('/ModoSmartphone')
def ModoMovil():
    return render_template('movil.html')


############################################################################################################

############################################################################################################


import time
@main.route('/conexion_dron', methods=['POST'])
def conexion_dron():
    try:
        comando = {
            "action": "conectar"
        }
        if publish_command(comando):
            time.sleep(0.5)
            from app.ModoGlobal import ultima_respuesta
            if ultima_respuesta:
                print(f"Respuesta de conexión: {ultima_respuesta}")
                return jsonify(ultima_respuesta), 200
            return jsonify({"estado": "error", "mensaje": "No se recibió respuesta"}), 500
        return jsonify({"estado": "error", "mensaje": "Error al enviar comando MQTT"}), 500
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

######################################################################

@main.route('/armar', methods=['POST'])
def armar():
    comando = {
        "action": "despegar",
        "altura": 0
    }
    if publish_command(comando):
        return jsonify({"estado": "success"}), 200
    return jsonify({"estado": "error"}), 500

######################################################################

@main.route('/despegar', methods=['POST'])
def despegar():
    try:
        data = request.get_json()
        metros = int(data.get('metros', 3))
        comando = {
            "action": "despegar",
            "altura": metros
        }
        if publish_command(comando):
            time.sleep(0.5)
            from app.ModoGlobal import ultima_respuesta
            if ultima_respuesta:
                print(f"Respuesta de despegue: {ultima_respuesta}")
                return jsonify(ultima_respuesta), 200
            return jsonify({"estado": "error", "mensaje": "No se recibió respuesta"}), 500
        return jsonify({"estado": "error", "mensaje": "Error al enviar comando MQTT"}), 500
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

######################################################################

@main.route('/aterrizar', methods=['POST'])
def aterrizar():
    try:
        comando = {
            "action": "aterrizar"
        }
        if publish_command(comando):
            time.sleep(0.5)
            from app.ModoGlobal import ultima_respuesta
            if ultima_respuesta:
                print(f"Respuesta de aterrizaje: {ultima_respuesta}")
                return jsonify(ultima_respuesta), 200
            return jsonify({"estado": "error", "mensaje": "No se recibió respuesta"}), 500
        return jsonify({"estado": "error", "mensaje": "Error al enviar comando MQTT"}), 500
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

######################################################################

@main.route('/desconectar_dron', methods=['POST'])
def desconectar():
    try:
        comando = {
            "action": "desconectar"
        }
        if publish_command(comando):
            time.sleep(0.5)
            from app.ModoGlobal import ultima_respuesta
            if ultima_respuesta:
                print(f"Respuesta de desconexión: {ultima_respuesta}")
                return jsonify(ultima_respuesta), 200
            return jsonify({"estado": "error", "mensaje": "No se recibió respuesta"}), 500
        return jsonify({"estado": "error", "mensaje": "Error al enviar comando MQTT"}), 500
    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

######################################################################

@main.route('/start_movement', methods=['POST'])
def start_movement():
    data = request.get_json()
    direction = data.get('direction')
    if not direction:
        return jsonify({'estado': 'error', 'message': 'Dirección no especificada'}), 400

    comando = {
        "action": "mover",
        "direccion": direction,
        "metros": 3
    }
    if publish_command(comando):
        return jsonify({"estado": "success"}), 200
    return jsonify({"estado": "error"}), 400

@main.route('/coordenadas', methods=['GET'])
def coordenadas():
    from app.ModoGlobal import telemetria_actual
    lat = telemetria_actual.lat
    lon = telemetria_actual.lon
    alt = telemetria_actual.alt
    resultado = {"lat": lat, "lon": lon, "alt": alt}
    return jsonify(resultado), 200 if "error" not in resultado else 500

####################################################################################################################################

@main.route('/telemetria', methods=['GET'])
def obtener_telemetria():
    from app.ModoGlobal import telemetria_actual
    return jsonify({"estado": "success", "data": telemetria_actual}), 200

####################################################################################################################################
@main.route('/start_movement2', methods=['POST'])
def start_movement2():
    data = request.get_json()
    direction = data.get('direction')
    if not direction:
        return jsonify({"estado": "error", "mensaje": "Dirección no especificada"}), 400

    comando = {
        "action": "mover",
        "direccion": direction,
        "metros": 1
    }

    publicado = publish_command(comando)
    if not publicado:
        return jsonify({"estado": "error", "mensaje": "No se pudo publicar el comando"}), 400

    return jsonify({"estado": "success"}), 200

######################################################################

@main.route('/detener_movimiento', methods=['POST'])
def detener_movimiento():
    publicado = publish_command("detener_dron")
    if not publicado:
        return jsonify({"estado": "error", "mensaje": "No se pudo publicar el comando"}), 400

    return jsonify({"estado": "success"}), 200

######################################################################
######################################################################

@main.route('/cambiar_estado2', methods=['POST'])
def cambiar_estado2():
    try:
        data = request.get_json()
        estado = data.get('estado')

        if not estado:
            return jsonify({"estado": "error", "message": "No se proporcionó un estado válido"}), 400

        resultado = publish_command("cambiar_estado")


        if not resultado:
            return jsonify({"estado": "error", "message": "No se pudo publicar el comando"}), 500

        return jsonify(resultado), 200 if resultado.get("estado") == "success" else 500
    except Exception as e:
        return jsonify({"estado": "error", "message": f"Error en el servidor: {str(e)}"}), 500


####################################################################################################################################

@main.route('/cambiar_tema_educativo', methods=['POST'])
def cambiar_tema_educativo():
    data = request.get_json()
    tema = data.get('tema')
    if tema:
        voice_control_service.modo_educativo = True
        #preguntas_controller.set_tema(tema)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Tema no especificado"}), 400




####################################################################################################################################

@main.route('/ejecutar_comando_educativo', methods=['POST'])
def ejecutar_comando_educativo():
    data = request.get_json()
    comando = data.get('comando')
    return jsonify({"status": "success"})

####################################################################################################################################
def procesar_comando_dron(comando): #quitar de aqui y ponerlo en algun servicio
        """Función auxiliar para procesar comandos del dron"""
        resultado = voice_control_service.procesar_respuesta(comando)
        mensaje = resultado.get("message", "")

        return jsonify({
            "estado": resultado.get("estado", "success"),
            "message": mensaje,
            "audio_url": voice_control_service.text_to_speech(mensaje),
            "comando_pendiente": resultado.get("comando_pendiente"),
            "es_respuesta_ia": resultado.get("es_respuesta_ia", True)
        })
####################################################################################################################################
####################################################################################################################################

######################################################################
@main.route('/procesar_plan_vuelo', methods=['POST'])
def procesar_plan():
    try:
        data = request.json
        comando = data.get('comando')

        voice_control_service.cambiar_personalidad("usuario_demo", "plan_vuelo")

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": PERSONALIDADES["plan_vuelo"]},
                {"role": "user", "content": comando}
            ],
            max_tokens=1500,
            temperature=0.3
        )

        respuesta = response.choices[0].message.content.strip()

        voice_control_service.cambiar_personalidad("usuario_demo", "normal")

        print(f"Respuesta IA completa: {respuesta}")

        try:
            if '{' in respuesta and '}' in respuesta:
                json_str = respuesta[respuesta.index('{'):respuesta.rindex('}')+1]
                plan = json.loads(json_str)

                if plan.get('type') != 'flightPlan' or not isinstance(plan.get('waypoints'), list):
                    return jsonify({"error": "Formato de plan inválido"}), 400

                return jsonify(plan), 200
            else:
                return jsonify({"error": "No se encontró JSON válido en la respuesta"}), 400

        except json.JSONDecodeError as e:
            print(f"Error al parsear JSON: {str(e)}")
            return jsonify({"error": "Error al procesar el plan"}), 400

    except Exception as e:
        print(f"Error en procesar_plan: {str(e)}")
        return jsonify({"error": f"Error al procesar el plan: {str(e)}"}), 500

######################################################################
@main.route('/ejecutar_plan_vuelo', methods=['POST'])
def ejecutar_plan():
    try:
        from app.ModoGlobal import publish_command

        plan = request.json
        waypoints = plan.get('waypoints', plan) if isinstance(plan, dict) else plan

        print(f"Plan recibido: {waypoints}")

        mission = crear_mision({"waypoints": waypoints})
        if mission:
            comando = {
                "action": "ejecutar_mision",
                "mission": mission
            }
            print(f"Enviando comando MQTT: {comando}")
            if publish_command(comando):
                return jsonify({"estado": "success"}), 200
            return jsonify({"estado": "error", "mensaje": "Error al enviar comando MQTT"})
        return jsonify({"estado": "error", "mensaje": "Error al crear la misión"})
    except Exception as e:
        print(f"Error en ejecutar_plan: {str(e)}")
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

######################################################################


@main.route('/check_broker', methods=['GET'])
def check_broker():
    from app.ModoGlobal import mqtt_client_instance
    if mqtt_client_instance and mqtt_client_instance.is_connected():
        return jsonify({"connected": True}), 200
    return jsonify({"connected": False}), 200

######################################################################
@main.route('/text_to_speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get('text', '')

        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang='es', slow=False)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        audio_base64 = base64.b64encode(mp3_fp.read()).decode()
        return jsonify({
            'estado': 'success',
            'audio_url': f"data:audio/mp3;base64,{audio_base64}"
        })
    except Exception as e:
        return jsonify({
            'estado': 'error',
            'mensaje': str(e)
        })


######################################################################
from app.audio_processor import AudioProcessor

@main.route('/procesar_audio_cliente', methods=['POST'])
def procesar_audio_cliente():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No se encontró el archivo de audio'}), 400

        try:
            audio_processor = AudioProcessor()
        except Exception as e:
            print(f"Error al inicializar AudioProcessor: {str(e)}")
            return jsonify({'error': f'Error al inicializar el procesador de audio: {str(e)}'}), 500

        audio_file = request.files['audio']

        try:

            audio_data = audio_file.read()

            result = audio_processor.process_audio(audio_data)

            if result['success']:
                return jsonify({
                    'transcription': result['transcription']
                })
            else:
                return jsonify({
                    'error': result['error']
                }), 500

        except Exception as e:
            print(f"Error procesando audio: {str(e)}")
            return jsonify({'error': f'Error procesando audio: {str(e)}'}), 500

    except Exception as e:
        print(f"Error general en procesar_audio_cliente: {str(e)}")
        return jsonify({'error': f'Error general: {str(e)}'}), 500



######################################################################
@main.route('/rotar', methods=['POST'])
def rotar():
    try:
        data = request.get_json()
        grados = data.get('grados')
        comando = {
            "action": "rotar",
            "grados": grados
        }
        publicado = publish_command(comando)

        if not publicado:
            return jsonify({"estado": "error", "mensaje": "No se pudo publicar el comando"}), 400

        return jsonify({"estado": "success"}), 200

    except Exception as e:
        return jsonify({"estado": "error", "mensaje": str(e)}), 500

############### Comunicacion Camara por Websocket ######################
@socketio.on('frame_Websocket')
def handle_video_frame(data):
    global recording, video_writer, filepath, taking_photo
    global expected_height, expected_width
    print("recibo frame de la estacion de tierra")
    socketio.emit('frame_Websocket_from_ground', data)
    try:
        # Decodifica el frame siempre
        img_data = base64.b64decode(data.split(',')[-1])
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if recording:
            if video_writer is None:
                height, width, _ = frame.shape
                expected_height, expected_width = height, width
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                directorio_base = os.path.dirname(os.path.abspath(__file__))
                carpeta_videos = os.path.join(directorio_base, 'videos')
                if not os.path.exists(carpeta_videos):
                    os.makedirs(carpeta_videos)
                filepath = os.path.join(carpeta_videos, filename)
                fourcc = cv2.VideoWriter_fourcc(*'avc1')
                video_writer = cv2.VideoWriter(filepath, fourcc, 10.0, (width, height))

            if frame is None:
                print("Frame inválido")
            else:
                if frame.shape[0] != expected_height or frame.shape[1] != expected_width:
                   frame = cv2.resize(frame, (expected_width, expected_height))
                video_writer.write(frame)

        if taking_photo:
            directorio_base = os.path.dirname(os.path.abspath(__file__))
            carpeta_fotos = os.path.join(directorio_base, 'fotos')

            if not os.path.exists(carpeta_fotos):
                os.makedirs(carpeta_fotos)

            filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = os.path.join(carpeta_fotos, filename)

            cv2.imwrite(filepath, frame)
            print(f"Foto guardada en: {filepath}")

            taking_photo = False

    except Exception as e:
        print(f"Error al grabar/tomar foto: {e}")
@socketio.on('start_recording')
def start_recording():
    global recording
    # Informo a estacion tierra para que grabe
    comando = {
        "action": "startRecord"
    }
    publish_command(comando)

    print(f"Iniciando grabación")
    recording = True




@socketio.on('stop_recording')
def stop_recording():
    global recording, video_writer, filepath
    print("Fin de grabación")
    comando = {
        "action": "stopRecord"
    }
    publish_command(comando)
    recording = False
    if video_writer:
        video_writer.release()
        print(f"Video guardado en: {filepath}")
        socketio.emit('video_ready', {'url': f"/videos/{os.path.basename(filepath)}"})
        video_writer = None


@socketio.on("foto_desde_estacion")
def recibir_foto(data):
    print("Evento recibido con foto:", data.get("nombre"))
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    CARPETA_DESTINO = os.path.join(directorio_actual, "fotos")
    os.makedirs(CARPETA_DESTINO, exist_ok=True)

    nombre = data.get("nombre", "foto_desconocida.jpg")
    contenido = base64.b64decode(data["contenido"])
    ruta_guardado = os.path.join(CARPETA_DESTINO, nombre)

    with open(ruta_guardado, "wb") as f:
        f.write(contenido)

    print(f"Foto recibida y guardada: {ruta_guardado}")
    return "OK"
# Envia al Javascript una foto en especifica
@main.route('/fotos/<path:filename>')
def servir_foto(filename):
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    CARPETA_FOTOS = os.path.join(directorio_actual, "fotos")
    return send_from_directory(CARPETA_FOTOS, filename)

# Envia al Javascript la lista de imagenes a enseñar
@main.route('/lista_fotos')
def lista_fotos():
    import os
    fotos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fotos")
    fotos = [f for f in os.listdir(fotos_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    return jsonify(fotos)

@socketio.on("video_desde_estacion")
def recibir_video(data):
    try:
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
        CARPETA_DESTINO = os.path.join(directorio_actual, "videos")
        os.makedirs(CARPETA_DESTINO, exist_ok=True)

        nombre = data.get("nombre", "video_desconocido.mp4")
        contenido_b64 = data.get("contenido")
        if contenido_b64 is None:
            print("No se recibió contenido para el video.")
            return "Error: no hay contenido"

        contenido = base64.b64decode(contenido_b64)  # Decodificamos de base64
        ruta_guardado = os.path.join(CARPETA_DESTINO, nombre)

        with open(ruta_guardado, "wb") as f:
            f.write(contenido)

        print(f"Video recibido y guardado: {ruta_guardado}")
        return "Video recibido correctamente"
    except Exception as e:
        print(f"Error al guardar el video: {e}")
        return f"Error: {e}"

@main.route('/videos/<path:filename>')
def servir_video(filename):
    videos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    print(f"Petición para video: {filename} en ruta: {videos_path}")
    return send_from_directory(videos_path, filename)

@main.route('/lista_videos')
def lista_videos():
    videos_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")
    videos = [f for f in os.listdir(videos_path) if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    return jsonify(videos)


@socketio.on('foto')
def foto():
    global taking_photo
    comando = {
        "action": "foto"
    }
    publicado = publish_command(comando)
    taking_photo = True
    if not publicado:
        return jsonify({"estado": "error", "mensaje": "No se pudo publicar el comando"}), 400
    return jsonify({"estado": "success"}), 200

@main.route('/actualizarmedia', methods=['POST'])
def actualizarmedia():
    comando = {
        "action": "actualizarmedia"
    }
    publicado = publish_command(comando)
    if not publicado:
        return jsonify({"estado": "error", "mensaje": "No se pudo publicar el comando"}), 400
    return jsonify({"estado": "success"}), 200


