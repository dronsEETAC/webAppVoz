from app import create_app, socketio
from flask_socketio import SocketIO
import os
import sys
import subprocess
import shutil
app = create_app()


def kill_process_using_port(port: int):
    """Mata todos los procesos que están usando un puerto específico."""
    try:
        if sys.platform.startswith("win"):  # Windows
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if f":{port} " in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True)
                    print(f"Proceso con PID {pid} terminado.")
        else:  # Linux / Mac
            result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "LISTEN" in line:
                    pid = line.split()[1]
                    subprocess.run(["kill", "-9", pid], capture_output=True, text=True)
                    print(f"Proceso con PID {pid} terminado.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    #app.run(debug=True)
    #app.run(host='0.0.0.0', port=5000, debug=True) #para movil

    ruta_carpeta_fotos = "/root/marina/RepoTFG/WebAppHTTP/app/fotos"
    ruta_carpeta_videos = "/root/marina/RepoTFG/WebAppHTTP/app/videos"

    if os.path.isdir(ruta_carpeta_fotos):
       shutil.rmtree(ruta_carpeta_fotos)

    if os.path.isdir(ruta_carpeta_videos):
       shutil.rmtree(ruta_carpeta_videos)

    os.makedirs(ruta_carpeta_fotos, exist_ok=True)
    os.makedirs(ruta_carpeta_videos, exist_ok= True)

    from threading import Thread

    # Pongo en marcha el servidor flask en un hilo separado
    # Uso el el puerto 5000 para el servidor en desarrollo
    # y el puerto 8104 para el servidor en producción (que es uno de los puertos abiertos en dronseetac.upc.edu)
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8104, debug=True, use_reloader=False,
       ssl_context=('/etc/letsencrypt/live/dronseetac.upc.edu/cert.pem', '/etc/letsencrypt/live/dronseetac.upc.edu/privkey.pem')))
    flask_thread.start()
    # liberamos el puerto que usaré el websocket
    print("Puerto liberado")
    # Pongo en marcha el websocket
    # Uso  el puerto 8766 para el servidor en desarrollo
    # y el puerto 8106 para el servidor en producción (que es uno de los puertos abiertos en dronseetac.upc.edu9
    socketio.run(app, host='0.0.0.0', port=8106, allow_unsafe_werkzeug=True)

