import math
from app.ModoGlobal import telemetria_actual
from dronLink.Dron import Dron
import time

dron = Dron()


def crear_mision(waypoints):
   print(f"Waypoints recibidos en crear_mision: {waypoints}")

   if isinstance(waypoints, dict):
       waypoints = waypoints.get('waypoints', [])

   mission = {
       "takeOffAlt": 3,
       "waypoints": []
   }

   try:
       from app.ModoGlobal import telemetria_actual
       telemetry = telemetria_actual

       '''if telemetry["state"] != "connected":
           raise ValueError("No se pudo obtener la telemetría del dron")'''
           
       current_heading = telemetry["heading"]
       current_lat = telemetry["lat"]
       current_lon = telemetry["lon"]

       for wp in waypoints:
           if wp['action'] == 'move':
               dir_lower = wp['direction'].lower()
               distance = wp['distance']

               if dir_lower in ['forward', 'back', 'left', 'right']:
                   # movimientos relativos al heading
                   if dir_lower == 'right':
                       bearing = (current_heading + 90) % 360
                   elif dir_lower == 'left':
                       bearing = (current_heading - 90) % 360
                   elif dir_lower == 'back':
                       bearing = (current_heading + 180) % 360
                   else:  # forward
                       bearing = current_heading

                   #calcula nueva posición
                   d = float(distance)
                   lat1 = math.radians(current_lat)
                   lon1 = math.radians(current_lon)
                   bearing_rad = math.radians(bearing)
                   R = 6378137.0

                   lat2 = math.asin(
                       math.sin(lat1) * math.cos(d/R) + 
                       math.cos(lat1) * math.sin(d/R) * math.cos(bearing_rad)
                   )

                   lon2 = lon1 + math.atan2(
                       math.sin(bearing_rad) * math.sin(d/R) * math.cos(lat1),
                       math.cos(d/R) - math.sin(lat1) * math.sin(lat2)
                   )

                   # waypoints
                   mission['waypoints'].append({
                       'lat': math.degrees(lat2),
                       'lon': math.degrees(lon2),
                       'alt': mission['takeOffAlt']
                   })
                   
                   current_lat = math.degrees(lat2)
                   current_lon = math.degrees(lon2)

               else:
                   # manejo de direcciones cardinales
                   new_pos = calcular_nueva_posicion(
                       current_lat, current_lon,
                       wp['direction'], wp['distance']
                   )
                   mission['waypoints'].append({
                       'lat': new_pos['lat'],
                       'lon': new_pos['lon'],
                       'alt': mission['takeOffAlt']
                   })
                   current_lat = new_pos['lat']
                   current_lon = new_pos['lon']
                   
           elif wp['action'] == 'rotate':
                if wp.get('clockwise', True):
                    dir = 1  # clockwise
                else:
                    dir = -1  # counter-clockwise
                    
                mission['waypoints'].append({
                    'rotRel': wp['degrees'],
                    'dir': dir
                })
                current_heading = (current_heading + (wp['degrees'] * dir)) % 360

       print(f"Misión creada: {mission}")
       return mission
       
   except Exception as e:
       print(f"Error creando misión: {str(e)}")
       print(f"Error creando misión: {str(telemetry)}")
       return None
    
def calcular_nueva_posicion(lat, lon, direccion, distancia, current_heading=None):
    R = 6378137.0
    d = float(distancia)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)

    dir_lower = direccion.lower()
    if current_heading is None:
        telemetry = telemetria_actual
        if telemetry["state"] == "connected":
            current_heading = telemetry["heading"]
        else:
            current_heading = 0


    if dir_lower == 'forward':
        # heading actual directamente para forward
        bearing = current_heading
    elif dir_lower == 'back':
        bearing = (current_heading + 180) % 360
    elif dir_lower == 'left':
        bearing = (current_heading - 90) % 360
    elif dir_lower == 'right':
        bearing = (current_heading + 90) % 360
    else:
        #direcciones cardinales absolutas
        bearings = {
            'north': 0,
            'northeast': 45,
            'east': 90,
            'southeast': 135,
            'south': 180,
            'southwest': 225,
            'west': 270,
            'northwest': 315
        }
        bearing = bearings.get(dir_lower, 0)

    bearing_rad = math.radians(bearing)

    #clculo de nueva posición
    lat2 = math.asin(
        math.sin(lat1) * math.cos(d/R) + 
        math.cos(lat1) * math.sin(d/R) * math.cos(bearing_rad)
    )

    lon2 = lon1 + math.atan2(
        math.sin(bearing_rad) * math.sin(d/R) * math.cos(lat1),
        math.cos(d/R) - math.sin(lat1) * math.sin(lat2)
    )

    return {
        'lat': math.degrees(lat2),
        'lon': math.degrees(lon2)
    }