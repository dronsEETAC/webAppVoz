from dronLink.Dron import Dron
from paho.mqtt import client as mqtt_client
import random
import time
import json
global ultima_respuesta
global mqtt_client_instance
dron = Dron()

ultima_respuesta = None
mqtt_client_instance = None
broker = 'broker.emqx.io'
port = 1883
topic = "smartphone/commands"
client_id = f'python-mqtt-{random.randint(0, 1000)}'

#########    FUNCIONES RELACIONADAS CON MQTT   #############################################################

def connect_mqtt():
    """Establece la conexión con el broker MQTT"""
    global mqtt_client_instance

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
        mqtt_client_instance = mqtt_client.Client(client_id)
        mqtt_client_instance.connected_flag = False
        mqtt_client_instance.on_connect = on_connect
        mqtt_client_instance.on_message = on_message

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

        '''print("DEBUG connect_mqtt: Timeout esperando conexión")
        mqtt_client_instance.loop_stop()
        mqtt_client_instance = None
        return None'''

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
                return False

            time.sleep(0.5)

        if isinstance(comando, dict):
            comando = json.dumps(comando)

        print(f"DEBUG publish_command: Publicando comando: {comando}")
        result = mqtt_client_instance.publish(topic, comando)

        if result.rc == 0:
            '''print("DEBUG publish_command: Comando publicado exitosamente")'''
            return True
        else:
            print(f"DEBUG publish_command: Error al publicar comando, código: {result.rc}")
            return False

    except Exception as e:
        print(f"DEBUG publish_command: Error al publicar comando: {str(e)}")
        return False



def on_message(client, userdata, msg):
    """Maneja los mensajes recibidos del broker MQTT"""
    global ultima_respuesta
    try:
        payload = json.loads(msg.payload.decode())
        comando = payload.get('comando') or payload.get('action')
        print(f"Comando recibido broker: {comando}")

        if comando == "conectar":
            print("DRON INTENTANDO CONECTAR MEDIANTE BROKER")
            result = conectar_dron()
            print(f"DEBUG on_message: Resultado de conectar_dron: {result}")
            ultima_respuesta = result
            print(f"DEBUG on_message: ultima_respuesta actualizada a {ultima_respuesta}")
            print('pido datos de telemetria')
            dron.send_telemetry_info(procesarTelemetria)
            comando = {
                    "action": "conectar_s",
                    "resultado": result,
            }
            publish_command(comando)

        elif comando == "despegar":
            altura = payload.get('altura', 5)
            result = armar_y_despegar(altura)
            ultima_respuesta = result
            comando = {
                "action": "despegar_s",
                "resultado": result,
            }
            publish_command(comando)

        elif comando == "aterrizar":
            result = aterrizar_dron()
            ultima_respuesta = result
            comando = {
                "action": "aterrizar_s",
                "resultado": result,
            }
            publish_command(comando)

        elif comando == "desconectar":
            result = desconectar_dron()
            ultima_respuesta = result
            comando = {
                "action": "desconectar_s",
                "resultado": result,
            }
            publish_command(comando)

        elif comando == "mover":
            direccion = payload.get('direccion')
            metros = payload.get('metros', 3)
            if not direccion:
                ultima_respuesta = {"estado": "error", "mensaje": "Dirección no especificada"}
                comando = {
                    "action": "mover_s",
                    "resultado": ultima_respuesta,
                }
                publish_command(comando)
            else:
                result = mover_dron(direccion, metros)
                ultima_respuesta = result
                comando = {
                    "action": "mover_s",
                    "resultado": result,
                }
                publish_command(comando)

        elif comando == "rotar":
            heading = payload.get('grados')
            if not heading:
                ultima_respuesta = {"estado": "error", "mensaje": "Grados no especificada"}
                comando = {
                    "action": "rotar_s",
                    "resultado": ultima_respuesta,
                }
                publish_command(comando)
            else:
                result = rotar_dron(heading)
                ultima_respuesta = result
                comando = {
                    "action": "rotar_s",
                    "resultado": result,
                }
                publish_command(comando)

        elif comando == "ejecutar_mision":
            mission = payload.get('mission')
            if mission:
                result = ejecutar_mision(mission)
                ultima_respuesta = result
                comando = {
                    "action": "ejecutar_mision_s",
                    "resultado": result,
                }
                publish_command(comando)
            else:
                ultima_respuesta = {"estado": "error", "mensaje": "Misión no especificada"}
                comando = {
                    "action": "ejecutar_mision_s",
                    "resultado": ultima_respuesta,
                }
                publish_command(comando)
        elif comando == "detener_dron":
            result = detener_dron()
            ultima_respuesta = result
            comando = {
                "action": "detener_dron_s",
                "resultado": result,
            }
            publish_command(comando)
        elif comando == "cambiar_estado":
            result = cambiar_estado()
            ultima_respuesta = result
            comando = {
                "action": "cambiar_estado_s",
                "resultado": result,
            }
            publish_command(comando)
        else:
            ultima_respuesta = {"estado": "error", "mensaje": "Comando no reconocido"}

            print(f"DEBUG on_message: Respuesta final establecida: {ultima_respuesta}")

    except Exception as e:
        print(f"Error en on_message: {str(e)}")
        ultima_respuesta = {"estado": "error", "mensaje": str(e)}
        print(f"DEBUG on_message: Error respuesta: {ultima_respuesta}")

def procesarTelemetria(telemetryInfo):
    publish_command({
        "comando": "obtener_telemetria_s",
        "data": telemetryInfo
    })

#########    FUNCIONES RELACIONADAS CON EL DRON  #############################################################

def conectar_dron():
    if dron.state != "connected":
        connection_string = 'tcp:127.0.0.1:5763'
        baud = 115200
        freq=10
        dron.connect(connection_string, baud)
        print("CONECTADOOOOOOOOOOOOOOOOOOOO")
        return {"estado": "success"}

    else:
        return {"estado": "error"}


def desconectar_dron():
    try:
        dron.disconnect()
        return {"estado": "success"}
    except Exception as e:
        return {"estado": "error"}


def armar_dron():
    print(dron.state)
    if dron.state == "connected" or dron.state == "arming" or dron.state == "armed" or dron.state == "takingOff" or dron.state == "landing":
        dron.arm(blocking=True)
        print(dron.state)
        return {"estado": "success"}
    else:
        print("error armar")
        return {"estado": "error"}


def despegar_dron(metros):
    print(dron.state)
    if dron.state != "armed":
        return {"estado": "error"}
    try:
        dron.takeOff(int(metros, blocking=True))
        return {"estado": "success"}
    except Exception as e:
        return {"estado": "error"}


def aterrizar_dron():
    print(dron.state)
    dron.Land(blocking=False)
    return {'estado': 'success', 'message': 'Dron aterrizado'}


def mover_dron(direccion, metros):
    print(dron.state)
    try:
        dron.move_distance(direccion, metros, blocking=False)
        return {'estado': 'success'}
    except Exception as e:
        return {'estado': 'error'}


def cambiar_estado(estado):
    print(f"Estado anterior: {dron.state}")
    try:
        dron.state = estado
        print(f"Estado cambiado a: {dron.state}")
        return {'estado': 'success'}
    except Exception as e:
        return {'estado': 'error'}


def detener_dron():
    try:

        dron.setMoveSpeed(0)
        return {'estado': 'success'}
    except Exception as e:
        return {'estado': f'Error al detener el movimiento del dron: {e}'}


def obtener_coordenadas():
    try:
        lat = dron.lat
        lon = dron.lon
        alt = dron.alt
        return {"lat": lat, "lon": lon, "alt": alt}
    except Exception as e:
        return {"error": f"Error al obtener las coordenadas: {str(e)}"}


def armar_y_despegar(metros):
    try:
        print("armar_y_despegar ejecutado")
        armar_dron()
        if dron.state != "armed":
            return {"estado": "error"}
        try:
            dron.takeOff(metros, blocking=False)
            return {"estado": "success"}
        except Exception as e:
            return {"estado": "error"}

    except Exception as e:
        return {"estado": "error"}


def rotar_dron(grados):
    try:
        heading_actual = dron.heading
        nuevo_heading = (heading_actual + grados) % 360
        dron.changeHeading(nuevo_heading)
        return {"estado": "success"}
    except Exception as e:
        print(f"Error al rotar el dron: {e}")
        return {"estado": "error"}


def ejecutar_mision(mission):
    """Ejecuta la misión proporcionada, manejando tanto waypoints como rotaciones"""
    try:
        print("Iniciando ejecución de misión")

        if mission['waypoints']:
            mission_waypoints = {
                "takeOffAlt": mission['takeOffAlt'],
                "waypoints": mission['waypoints']
            }
            dron.uploadMission(mission_waypoints)
            dron.executeMission(blocking=False)

        if 'rotations' in mission and mission['rotations']:
            for rotation in mission['rotations']:
                print(f"Rotando {rotation['degrees']} grados")
                dron.changeHeading(rotation['degrees'])

        return {"estado": "success"}
    except Exception as e:
        print(f"Error ejecutando misión: {str(e)}")
        return {"estado": "error", "mensaje": str(e)}

######### EJECUCIÓN DEL PROGRAMA #########################################

mqtt_client_instance = connect_mqtt()
print('Esperando peticiones ')
while True:
    time.sleep(1)








