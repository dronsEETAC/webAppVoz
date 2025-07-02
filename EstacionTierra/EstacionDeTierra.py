from paho.mqtt.subscribe import callback
from dronLink.Dron import Dron
from paho.mqtt import client as mqtt_client
import random
import time
import json
import os
global ultima_respuesta
global modo
global brk
global ip_websocket
global mqtt_client_instance
global grabando
global cam
global sio
global frame_actual
import threading
import socketio
import cv2
global sendingWebsockets
global cap
import base64
from PIL import Image, ImageTk
import tkinter as tk
dron = Dron()

ultima_respuesta = None
mqtt_client_instance = None
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


        if brk == "s":
            mqtt_client_instance = mqtt_client.Client(client_id, transport="websockets")
            mqtt_client_instance.connected_flag = False
            mqtt_client_instance.on_connect = on_connect
            mqtt_client_instance.on_message = on_message
            broker = 'dronseetac.upc.edu'
            port = 8000

            mqtt_client_instance.username_pw_set (
                'dronsEETAC', 'mimara1456.'
            )
        else:
            mqtt_client_instance = mqtt_client.Client(client_id)
            mqtt_client_instance.connected_flag = False
            mqtt_client_instance.on_connect = on_connect
            mqtt_client_instance.on_message = on_message
            broker = 'broker.emqx.io'
            port = 1883

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
    global grabando, contVideos, out
    global cont, lastFrame
    global nombresoloarchivo
    import time
    try:
        payload = json.loads(msg.payload.decode())
        comando = payload.get('comando') or payload.get('action')
        print(f"Comando recibido broker: {comando}")

        if comando == "conectar":
            print("DRON INTENTANDO CONECTAR MEDIANTE BROKER")
            result = conectar_dron()
            print(f"DEBUG on_message: Resultado de conectar_dron: {result}")
            ultima_respuesta = result
            print('pido datos de telemetria')
            dron.send_telemetry_info(procesarTelemetria)


        elif comando == "despegar":
            altura = payload.get('altura', 5)
            result = armar_y_despegar(altura)
            ultima_respuesta = result

        elif comando == "aterrizar":
            result = aterrizar_dron()
            ultima_respuesta = result

        elif comando == "desconectar":
            result = desconectar_dron()
            ultima_respuesta = result

        elif comando == "mover":
            direccion = payload.get('direccion')
            metros = payload.get('metros', 3)
            if not direccion:
                ultima_respuesta = {"estado": "error", "mensaje": "Dirección no especificada"}
            else:
                result = mover_dron(direccion, metros)
                ultima_respuesta = result

        elif comando == "rotar":
            heading = payload.get('grados')
            if not heading:
                ultima_respuesta = {"estado": "error", "mensaje": "Grados no especificada"}
            else:
                result = rotar_dron(heading)
                ultima_respuesta = result

        elif comando == "ejecutar_mision":
            mission = payload.get('mission')
            if mission:
                result = ejecutar_mision(mission)
                ultima_respuesta = result
            else:
                ultima_respuesta = {"estado": "error", "mensaje": "Misión no especificada"}

        elif comando == "detener_dron":
            result = detener_dron()
            ultima_respuesta = result

        elif comando == "cambiar_estado":
            result = cambiar_estado()
            ultima_respuesta = result

        elif comando == "foto":
            print("hago foto")
            local_time = time.localtime()
            tiempo = time.strftime('%Y-%m-%d_%H-%M-%S', local_time)
            print("Fecha y hora:", time.strftime('%Y-%m-%d %H:%M:%S', local_time))
            nombreFichero = "fotos/" + tiempo + ".jpg"
            cv2.imwrite(nombreFichero, lastFrame)

        elif comando == 'startRecord':
            print("Inicio grabacion")
            FPS = 10
            # añado los FPS al nombre del fichero porque necesitaré ese número en el momento
            # de la reproducción del vídeo
            local_time = time.localtime()
            tiempo = time.strftime('%Y-%m-%d_%H-%M-%S', local_time)
            nombreFicheroVideo = "videos/video" + tiempo + ".mp4"
            nombresoloarchivo = "video" + tiempo + ".mp4"
            # Obtener el ancho y alto del video
            ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Definir el codec y crear el objeto VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(nombreFicheroVideo, fourcc, FPS, (ancho, alto))
            grabando = True

        elif comando == 'stopRecord':
            try:
                grabando = False
                out.release()
                print(f"Grabación terminada: {nombresoloarchivo}")

            except Exception as e:
                print(f"Error al detener grabación: {e}")
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
        if modo == "s":
            print("Modo Simulacion activado")
            connection_string = 'tcp:127.0.0.1:5763'
            baud = 115200
        else:
            print("Modo Real activado")
            connection_string = 'COM8'
            baud = 57600
        freq = 10
        dron.connect(connection_string, baud, callback=enviar_respuesta("conectar_s", "success"))
        print("CONECTADOOOOOOOOOOOOOOOOOOOO")
        return {"estado": "success"}

    else:
        return {"estado": "error"}


def desconectar_dron():
    try:
        dron.disconnect(callback=enviar_respuesta("desconectar_s", "success"))
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
        dron.takeOff(int(metros, blocking=True), callback=lambda: enviar_respuesta("despegar_s", "success"))
        return {"estado": "success"}
    except Exception as e:
        return {"estado": "error"}


def aterrizar_dron():
    print(dron.state)
    dron.Land(blocking=False, callback=lambda: enviar_respuesta("aterrizar_s", "success"))

    return {'estado': 'success', 'message': 'Dron aterrizado'}


def mover_dron(direccion, metros):
    print(dron.state)
    try:
        dron.move_distance(direccion, metros, blocking=False, callback=lambda: enviar_respuesta("mover_s", "success"))
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
        dron.setMoveSpeed(0, callback=enviar_respuesta("destener_s", "success"))
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
        print(dron.state)
        armar_dron()
        try:
            dron.takeOff(metros, blocking=False, callback=lambda: enviar_respuesta("despegar_s", "success"))
            return {"estado": "success"}
        except Exception as e:
            return {"estado": "error"}

    except Exception as e:
        return {"estado": "error"}


def rotar_dron(grados):
    try:
        heading_actual = dron.heading
        nuevo_heading = (heading_actual + grados) % 360
        dron.changeHeading(nuevo_heading, callback= enviar_respuesta("rotar_s", "success"))
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

def enviar_respuesta(comando_accion, result):
    "Envia la respuesta de la acción al servidor"
    comando = {
        "action": comando_accion,
        "resultado": result,
    }
    publish_command(comando)

############ CAMARA WEBSOCKET #######################
def videoWebsockets():
    global sendingWebsockets
    global videoWebsocketBtn

    if sendingWebsockets:
        sendingWebsockets = False
    else:
        t = threading.Thread(target=video_Websocket_thread).start()

def video_Websocket_thread():
    global cap, sendingWebsockets, sio
    global lastFrame, grabando, frame_actual
    # Para escoger la calidad de video se deben tocar estos parámetros:
    frequency = 10
    quality = 50

    sendingWebsockets = True
    # espero el tiempo establecido según la frecuencia seleccionada
    periodo = 1 / frequency
    while sendingWebsockets:
        if frequency > 0:
            ret, frame = cap.read()
            if not ret:
                break
            lastFrame = frame
            frame_actual = frame.copy()
            if grabando:
                out.write(frame)
            # genero el frame con el nivel de calidad seleccionado (entre 0 y 100)
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            # envio el frame por el webbsocket
            if sio.connected:
                sio.emit('frame_Websocket', frame_b64)
            time.sleep(periodo)


######### EJECUCIÓN DEL PROGRAMA #########################################

'''brk = input("Quieres conectarte al broker de la UPC? (s/n)")
mqtt_client_instance = connect_mqtt()
modo = input("Vas a hacer una simulacion? (s/n)")

cap = cv2.VideoCapture(0)
sendingMQTT = False
sendingWebsockets = False
sio = socketio.Client()
grabando = False

try:
    sio.connect('http://dronseetac.upc.edu:8106')
    sio.connect('http://192.168.1.176:8767/')
    print("Conectado al servidor websocket")

except Exception as e:
    print("Error conectando:", e)

while not sio.connected:
    print("Esperando conexión WebSocket...")
    time.sleep(0.5)

videoWebsockets()
print('Esperando peticiones ')'''

def iniciar_estacion():
    global ip_websocket, cap, mqtt_client_instance, grabando, cam, sendingWebsockets, sio
    grabando = False
    sendingWebsockets = False
    try:
        mqtt_client_instance = connect_mqtt()

    except Exception as e:
        mensaje = "ERROR: No se ha podido conectar al Broker"
        color = "red"

    try:
        cap = cv2.VideoCapture(cam)

    except Exception as e:
        mensaje = "ERROR: No se ha podido conectar la camara"
        color = "red"
    try:
        sio = socketio.Client()
        sio.connect(ip_websocket)
        mensaje = "Conectado!"
        color = "green"
    except Exception as e:
        mensaje = "ERROR: No se ha podido realizar la conexión Websocket"
        color = "red"


    resultadoLbl = tk.Label(ventana, text=mensaje, fg=color, font=("Arial", 10, "bold"))
    resultadoLbl.grid(row=10, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

def cambiar_variable(accion):
    global brk, modo, ip_websocket, cam
    if accion == "brk_publico":
        brk = "n"
        r_brk_rLbl.config(text="Broker Público")
    elif accion == "brk_UPC":
        brk = "s"
        r_brk_rLbl.config(text="Broker UPC")
    elif accion == "simulacion":
        modo = "s"
        r_modo_rLbl.config(text="Simulacion")
    elif accion == "real":
        modo = "n"
        r_modo_rLbl.config(text="Real")
    elif accion == "cam_ordenador":
        cam = 0
        r_cam_rLbl.config(text="Ordenador")
    elif accion == "cam_dron":
        cam = 1
        r_cam_rLbl.config(text="Dron")
    else:
        ip_websocket = accion
        r_ip_rLbl.config(text=ip_websocket)



ventana = tk.Tk()
ventana.geometry ('900x400')
ventana.title("Estación de tierra")


ventana.rowconfigure(0, weight=1)
ventana.rowconfigure(1, weight=1)
ventana.rowconfigure(2, weight=1)
ventana.rowconfigure(3, weight=1)
ventana.rowconfigure(4, weight=1)
ventana.rowconfigure(5, weight=1)
ventana.rowconfigure(6, weight=1)
ventana.rowconfigure(7, weight=1)
ventana.rowconfigure(8, weight=1)



ventana.columnconfigure(0, weight=1)
ventana.columnconfigure(1, weight=1)
ventana.columnconfigure(2, weight=1)
ventana.columnconfigure(3, weight=1)


brokerLbl = tk.Label(ventana, text="¿A qué broker te quieres conectar?", font=("Arial", 12))
brokerLbl.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

brokerPublicoBtn = tk.Button(ventana, text="Broker público", bg="dark orange", command= lambda: cambiar_variable("brk_publico"))
brokerPublicoBtn.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

brokerUpcBtn = tk.Button(ventana, text="Broker UPC", bg="dark orange", command= lambda: cambiar_variable("brk_UPC"))
brokerUpcBtn.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

brokerLbl = tk.Label(ventana, text="Escoge el modo:", font=("Arial", 12))
brokerLbl.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

simulacionBtn = tk.Button(ventana, text="Simulacion", bg="dark orange", command= lambda: cambiar_variable("simulacion"))
simulacionBtn.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")

realBtn = tk.Button(ventana, text="Real", bg="dark orange", command=lambda: cambiar_variable("real"))
realBtn.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")

camaraLbl = tk.Label(ventana, text="Que cámara usarás?", font=("Arial", 12))
camaraLbl.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

ordenadorBtn = tk.Button(ventana, text="Camara Ordenador", bg="dark orange", command=lambda: cambiar_variable("cam_ordenador"))
ordenadorBtn.grid(row=5, column=0, padx=5, pady=5, sticky="nsew")

dronBtn = tk.Button(ventana, text="Camara Dron", bg="dark orange", command=lambda: cambiar_variable("cam_dron"))
dronBtn.grid(row=5, column=1, padx=5, pady=5, sticky="nsew")

brokerLbl = tk.Label(ventana, text="Escribe la dirección para WebSockets:", font=("Arial", 12))
brokerLbl.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

entrada = tk.Entry(ventana, width=40)
entrada.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

boton = tk.Button(ventana, text="Enviar", command=lambda: cambiar_variable(entrada.get()))
boton.grid(row=7, column=1, padx=5, pady=5)


r_brkLbl = tk.Label(ventana, text="Broker:", font=("Arial", 12))
r_brkLbl.grid(row=0, column=2, columnspan=1, padx=5, pady=5, sticky="nsew")

r_brk_rLbl = tk.Label(ventana, text="", font=("Arial", 12))
r_brk_rLbl.grid(row=0, column=3, columnspan=1, padx=5, pady=5, sticky="nsew")

r_modoLbl = tk.Label(ventana, text="Modo:", font=("Arial", 12))
r_modoLbl.grid(row=1, column=2, columnspan=1, padx=5, pady=5, sticky="nsew")

r_modo_rLbl = tk.Label(ventana, text="", font=("Arial", 12))
r_modo_rLbl.grid(row=1, column=3, columnspan=1, padx=5, pady=5, sticky="nsew")

r_camLbl = tk.Label(ventana, text="Camara:", font=("Arial", 12))
r_camLbl.grid(row=2, column=2, columnspan=1, padx=5, pady=5, sticky="nsew")

r_cam_rLbl = tk.Label(ventana, text="", font=("Arial", 12))
r_cam_rLbl.grid(row=2, column=3, columnspan=1, padx=5, pady=5, sticky="nsew")

r_ipLbl = tk.Label(ventana, text="IP Websocket:", font=("Arial", 12))
r_ipLbl.grid(row=3, column=2, columnspan=1, padx=5, pady=5, sticky="nsew")

r_ip_rLbl = tk.Label(ventana, text="", font=("Arial", 12))
r_ip_rLbl.grid(row=3, column=3, columnspan=1, padx=5, pady=5, sticky="nsew")

iniciarBtn = tk.Button(ventana, text="Iniciar Estacion Tierra", bg="dark orange", command=lambda: iniciar_estacion())
iniciarBtn.grid(row=4, column=2, columnspan= 1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

videoWebsocketBtn = tk.Button(ventana, text="Enviar video por websockets", bg="dark orange", command=lambda: videoWebsockets())
videoWebsocketBtn.grid(row=4, column=3, columnspan=1, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)



ventana.mainloop()








