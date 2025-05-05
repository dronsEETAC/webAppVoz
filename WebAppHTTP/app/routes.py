from flask import Blueprint, render_template, jsonify, request, send_from_directory
from app.voice_control import enviar_comando_openai, VoiceRecognitionSystem, PERSONALIDADES
from app.VoiceControlService import VoiceControlService
from app.plan_de_vuelo import crear_mision
from dronLink.Dron import Dron
from app.ModoGlobal import publish_command
from gtts import gTTS
from io import BytesIO
import base64
import openai
import json
import mimetypes
dron = Dron()
main = Blueprint('main', __name__)

voice_control_service = VoiceControlService()
conectado=False
armado=False
voice_recognition = VoiceRecognitionSystem("C:/Users/Mariina/Desktop/RepoTFG/victorsorolla-AI-Drone-Voice-Control/WebAppHTTP/vosk-model-small-es-0.42")


@main.route('/static/js/<path:filename>')
def serve_js(filename):
    mimetypes.add_type('application/javascript', '.js')  # Asegura que .js tenga el tipo MIME correcto
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

        # if voice_control_service.modo_educativo:
        #     print(f"Tema actual: {preguntas_controller.tema_actual}")

            
        #     if preguntas_controller.hay_pregunta_pendiente():
        #         print("Validando respuesta a pregunta pendiente")
        #         resultado = preguntas_controller.validar_respuesta(comando)
        #         if resultado["es_correcta"]:
        #             comando_pendiente = resultado["comando_pendiente"]
        #             print(f"Respuesta correcta - ejecutando comando: {comando_pendiente}")
        #             accion_resultado = voice_control_service.ejecutar_accion(comando_pendiente)
        #             mensaje = enviar_comando_openai(
        #                 voice_control_service.usuario_actual,
        #                 f"RESPUESTA CORRECTA: El usuario ha respondido correctamente. "
        #                 f"La acción {comando_pendiente} se ha ejecutado."
        #             )
        #             return jsonify({
        #                 "estado": "success",
        #                 "message": mensaje,
        #                 "audio_url": voice_control_service.text_to_speech(mensaje)
        #             })
        #         else:
        #             print("Respuesta incorrecta")
        #             mensaje = enviar_comando_openai(
        #                 voice_control_service.usuario_actual,
        #                 f"RESPUESTA INCORRECTA: La respuesta correcta era {resultado['respuesta_correcta']}. "
        #                 f"Anima al usuario a intentarlo de nuevo."
        #             )
        #             return jsonify({
        #                 "estado": "error",
        #                 "message": mensaje,
        #                 "audio_url": voice_control_service.text_to_speech(mensaje)
        #             })

           
        #     respuesta_ia = enviar_comando_openai(voice_control_service.usuario_actual, comando)
        #     print(f"Interpretación de la IA: {respuesta_ia}")

           
        #     for accion in voice_control_service.acciones_clave:
        #         if accion in respuesta_ia.lower():
        #             print(f"Acción detectada en respuesta IA: {accion}")
        #             # Generar pregunta educativa
        #             pregunta = preguntas_controller.generar_pregunta(accion)
        #             print(f"Generando pregunta para acción: {accion}")
                    
        #             if pregunta["status"] == "success":
        #                 mensaje_audio = f"{pregunta['pregunta']}. Las opciones son: {', '.join(pregunta['opciones'])}"
        #                 return jsonify({
        #                     "estado": "pregunta",
        #                     "pregunta": pregunta["pregunta"],
        #                     "opciones": pregunta["opciones"],
        #                     "audio_url": voice_control_service.text_to_speech(mensaje_audio)
        #                 })
        #             else:
        #                 print(f"Error al generar pregunta: {pregunta.get('message')}")
        #                 return jsonify({
        #                     "estado": "error",
        #                     "message": "Error al generar la pregunta educativa",
        #                     "audio_url": voice_control_service.text_to_speech("Error al generar la pregunta educativa")
        #                 })

           
            # return jsonify({
            #     "estado": "success",
            #     "message": respuesta_ia,
            #     "audio_url": voice_control_service.text_to_speech(respuesta_ia)
            # })

        # Modo normal (no educativo)
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
    
# @main.route('/ejecutar_plan_vuelo', methods=['POST'])
# def ejecutar_plan():
#     try:
#         plan = request.json
#         comando = {
#             "action": "ejecutar_mision",
#             "mission": {
#                 "waypoints": [
#                     {"action": "takeoff", "altitude": 3}  # Altura por defecto
#                 ]
#             }
#         }
        
#         
#         for wp in plan.get('waypoints', []):
#             if wp['action'] == 'move':
#                 comando['mission']['waypoints'].append(wp)
        
#         
#         comando['mission']['waypoints'].append({"action": "land"})
        
#         if publish_command(comando):
#             return jsonify({"estado": "success"}), 200
#         return jsonify({"estado": "error", "mensaje": "Error al enviar comando"}), 500
#     except Exception as e:
#         return jsonify({"estado": "error", "mensaje": str(e)}), 500

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