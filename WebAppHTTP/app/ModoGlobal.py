import random
import time
import json
from paho.mqtt import client as mqtt_client
global ultima_respuesta
global telemetria_actual
global resultado_accion
import threading

telemetria_actual = {
    "lat": 0,
    "lon": 0,
    "alt": 0,
    "groundSpeed": 0,
    "heading": "",
    "state": "",
    "flightmode": ""
}
ultima_respuesta = None
resultado_accion = None
evento_accion = threading.Event()
mqtt_client_instance = None
topic = "smartphone/commands"
client_id = f'python-mqtt-{random.randint(0, 1000)}'


def on_message(client, userdata, msg):
    """Maneja los mensajes recibidos del broker MQTT"""
    global ultima_respuesta
    global resultado_accion
    try:
        payload = json.loads(msg.payload.decode())
        comando = payload.get('comando') or payload.get('action')
        print(f"Comando recibido broker: {comando}")

        if comando == "conectar_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion


        elif comando == "despegar_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "aterrizar_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "desconectar_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "detener_dron_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "cambiar_estado_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "rotar_s" or comando == "mover_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "ejecutar_mision_s":
            resultado_accion = payload.get('resultado')
            evento_accion.set()
            print(f"DEBUG on_message: Resultado de la accion: {resultado_accion}")
            ultima_respuesta= resultado_accion

        elif comando == "obtener_telemetria_s":
            data = payload.get('data', {})
            if isinstance(data, dict):
                telemetria_actual.update(data)
            ultima_respuesta = {"estado": "success", "data": telemetria_actual}
        else:
            ultima_respuesta = {"estado": "error", "mensaje": "Comando no reconocido"}

        print(f"DEBUG on_message: Respuesta final establecida: {ultima_respuesta}")

    except Exception as e:
        print(f"Error en on_message: {str(e)}")
        ultima_respuesta = {"estado": "error", "mensaje": str(e)}
        print(f"DEBUG on_message: Error respuesta: {ultima_respuesta}")

def connect_mqtt():
    """Establece la conexión con el broker MQTT"""
    global mqtt_client_instance
    telemetry_info = None
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("DEBUG connect_mqtt: Conectado exitosamente al broker MQTT")
            client.subscribe(topic)
            print(f"DEBUG connect_mqtt: Suscrito al tópico '{topic}'")
            client.connected_flag = True
        else:
            print(f"DEBUG connect_mqtt: Fallo en conexión, código: {rc}")
            client.connected_flag = False
    try:
        if mqtt_client_instance and mqtt_client_instance.is_connected():
            print("DEBUG connect_mqtt: Ya existe una conexión activa")
            return mqtt_client_instance

        print("DEBUG connect_mqtt: Creando nueva conexión MQTT")
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        mqtt_client_instance = mqtt_client.Client(client_id, transport = "websockets")
        mqtt_client_instance.connected_flag = False
        mqtt_client_instance.on_connect = on_connect
        mqtt_client_instance.on_message = on_message

        broker = 'dronseetac.upc.edu'
        port = 8000

        mqtt_client_instance.username_pw_set (
                'dronsEETAC', 'mimara1456.'
        )

        print("DEBUG connect_mqtt: Intentando conectar al broker")
        mqtt_client_instance.connect(broker, port)
        mqtt_client_instance.loop_start()

        timeout = 5
        start_time = time.time()
        while time.time() - start_time < timeout:
            if hasattr(mqtt_client_instance, 'connected_flag') and mqtt_client_instance.connected_flag:
                print("DEBUG connect_mqtt: Conexión establecida exitosamente")
                return mqtt_client_instance
            time.sleep(0.1)

        print("DEBUG connect_mqtt: Timeout esperando conexión")
        mqtt_client_instance.loop_stop()
        mqtt_client_instance = None
        return None

    except Exception as e:
        print(f"DEBUG connect_mqtt: Error al conectar: {str(e)}")
        if mqtt_client_instance:
            mqtt_client_instance.loop_stop()
            mqtt_client_instance = None
        return None
def publish_command(comando):
    """Publica un comando en el broker MQTT"""
    global mqtt_client_instance

    try:
        if not mqtt_client_instance or not mqtt_client_instance.is_connected():
            print("DEBUG publish_command: Reconectando al broker MQTT")
            mqtt_client_instance = connect_mqtt()
            if not mqtt_client_instance:
                print("DEBUG publish_command: No se pudo establecer conexión MQTT")
                return {"estado": "error"}

            time.sleep(0.5)

        if isinstance(comando, dict):
            comando = json.dumps(comando)

        print(f"DEBUG publish_command: Publicando comando: {comando}")
        result = mqtt_client_instance.publish(topic, comando)

        if result.rc == 0:
            print("DEBUG publish_command: Comando publicado exitosamente")
            return {"estado": "success"}
        else:
            print(f"DEBUG publish_command: Error al publicar comando, código: {result.rc}")
            return {"estado": "success"}

    except Exception as e:
        print(f"DEBUG publish_command: Error al publicar comando: {str(e)}")
        return {"estado": "error"}

# LO QUE ANTES ESTABA EN DRON CONTROLS
def obtener_datos_telemetria():
    try:
        publish_command({"comando": "obtener_telemetria"})
        return {"estado": "success"}
    except Exception as e:
        return {"estado": "error", "message": str(e)}


