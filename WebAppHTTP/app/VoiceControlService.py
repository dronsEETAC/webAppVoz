from random import random
import time
from app.voice_control import enviar_comando_openai
from gtts import gTTS
from io import BytesIO
import base64
from text_to_num import text2num
import re
import app.ModoGlobal



class VoiceControlService:
    def __init__(self):
        self.estado_conversacion = None
        self.comando_pendiente = None
        self.valor_pendiente = None
        self.acciones_clave = [
            "conectar", "despegar", "aterrizar", 
            "avanzar", "retroceder", "derecha", "izquierda", 
            "subir", "bajar", "detener", "desconectar",
            "rotar", "rotar derecha", "rotar izquierda"
            "mover", "mover derecha", "mover izquierda"
        ]
        self.modo_educativo = False
        self.usuario_actual = "usuario_demo"
        #self.pregunta_actual = None  


    def procesar_comando_normal(self, comando):
        resultado = self.procesar_respuesta(comando)
        from app.voice_control import personalidad_actual

        if self.estado_conversacion == "pregunta_educativa":
            return resultado

        if (personalidad_actual == "pregunton" and 
            self.estado_conversacion != "pregunta_educativa" and 
            "correcto" in resultado.get("message", "").lower()):
            print("Respuesta correcta detectada en modo preguntón")
            return resultado  
        
        match resultado.get("estado"):
            case "confirmación":
                return {
                    "estado": "confirmación",
                    "message": resultado["message"],
                    "audio_url": self.text_to_speech(resultado["message"]),
                    "comando_pendiente": resultado.get("comando_pendiente")
                }

            case "confirmado":
                accion = resultado["comando"]
                respuesta_accion = self.ejecutar_accion(accion)
                return {
                    "estado": respuesta_accion.get("estado", "success"),
                    "message": respuesta_accion["message"],
                    "audio_url": self.text_to_speech(respuesta_accion["message"])
                }
            
            case _:
                #caso por defecto 
                mensaje = resultado.get("message", "Comando procesado")
                return {
                    "estado": resultado.get("estado", "success"),
                    "message": mensaje,
                    "audio_url": self.text_to_speech(mensaje)
                }


    def _extraer_valor_numerico(self, texto):#Extrae el primer número que vaya seguido de 'metro(s)' o 'grado(s)'
        try:
            texto = texto.lower().replace("ciento", "100")
            match_palabra = re.search(r'(\w+)\s*(metro|metros|grado|grados)', texto.lower())
            match_numero = re.search(r'(\d+)\s*(metro|metros|grado|grados)', texto.lower())
            if match_numero:
                # Si encontramos un número en dígitos, simplemente devolvemos el número
                return int(match_numero.group(1))  # Convertimos el número encontrado en dígitos a entero
            elif match_palabra:
                # Si encontramos un número en palabras, lo convertimos a número
                texto_convertido = text2num(match_palabra.group(1), lang="es")
                print(f"Texto convertido (de palabras): {texto_convertido}")
                return texto_convertido
            else:
                print(f"No se ha encontrado ningun numero")
                return None

        except Exception as e:
            print(f"Error al convertir el texto: {e}")
            return None
        
    def _detectar_accion_en_respuesta(self, respuesta):
        """Detecta si hay una acción en la respuesta de la IA"""
        respuesta_lower = respuesta.lower()
        print(f"Analizando respuesta para detectar acción: {respuesta_lower}") 
        
        if "rotar" in respuesta_lower or "girar" in respuesta_lower:
            if "derecha" in respuesta_lower:
                return "rotar derecha"
            elif "izquierda" in respuesta_lower:
                return "rotar izquierda"
            return "rotar"  # si no especifica dirección

        for accion in self.acciones_clave:
            if re.search(rf'\b{re.escape(accion)}\b', respuesta_lower):
                print(f"Acción detectada: {accion}")
                return accion
                
        print("No se detectó ninguna acción en la respuesta de IA")
        return None

    def procesar_respuesta(self, respuesta, es_confirmacion=False):
        from app.voice_control import personalidad_actual
        print("\n=== INICIO PROCESAR RESPUESTA ===")
        print(f"Respuesta recibida: {respuesta}")
        print(f"Es confirmación: {es_confirmacion}")
        print(f"Estado conversación: {self.estado_conversacion}")
        print(f"Comando pendiente: {self.comando_pendiente}, {self.valor_pendiente}")

        respuesta_lower = respuesta.lower().strip()

        if self.estado_conversacion == "pregunta_educativa":
            print(f"Respuesta del usuario: {respuesta}")
            respuesta_validacion = enviar_comando_openai(
                self.usuario_actual,
                f"VALIDAR_RESPUESTA: El usuario respondió: {respuesta}. "
                "Si la respuesta es correcta, genera una breve felicitación, amenzanado "
                "de futuras preguntas y termina el mensaje con '<!--CORRECTO--> sin hacer mas preguntas'. "
                "Si la respuesta es incorrecta, responde indicando que es incorrecta y haz una nueva"
                "pregunta educativa manteniendo el tono de profesor estricto."
            )
            print(f"Respuesta de validación completa: {respuesta_validacion}")
            print(f"Respuesta RAW de validación: [{respuesta_validacion}]")
            if "<!--CORRECTO-->" in respuesta_validacion:
                print("Respuesta educativa correcta => ejecutando acción pendiente")
                print(f"Mensaje de felicitación: {respuesta_validacion.replace('<!--CORRECTO-->', '').strip()}")
                #ejecutar la acción primero
                resultado_accion = self.ejecutar_accion(self.comando_pendiente, self.valor_pendiente)
                if resultado_accion["estado"] == "success":
                    #remover el marcador y mostrar solo la felicitación
                    mensaje_final = respuesta_validacion.replace("<!--CORRECTO-->", "").strip() #se elimina el marcador para que no se muestre ni lo "hable"
                    self._reset_estado()
                    return {
                        "estado": "success",
                        "message": mensaje_final,
                        "audio_url": self.text_to_speech(mensaje_final)
                    }
                return resultado_accion
            else:
                print("Respuesta educativa incorrecta => se muestra el mensaje con la corrección y se formula una nueva pregunta")
                return {
                    "estado": "pregunta_educativa",
                    "message": respuesta_validacion,
                    "comando_pendiente": self.comando_pendiente,
                    "audio_url": self.text_to_speech(respuesta_validacion)
                }

        if self.estado_conversacion == "confirmar_accion":
            if any(confirmacion in respuesta_lower for confirmacion in 
                ["sí", "si", "s", "yes", "y", "confirmar", "ok", "okay", "confirmo", "confirmó", "vale"]):
                print("Confirmación recibida => ejecutando acción")
                resultado = self.ejecutar_accion(self.comando_pendiente, self.valor_pendiente, es_confirmacion=True)
                self._reset_estado()
                return resultado

            elif any(negacion in respuesta_lower for negacion in 
                    ["no", "n", "cancelar", "detener"]):
                print("Acción cancelada por el usuario")
                mensaje = enviar_comando_openai(
                    self.usuario_actual,
                    "ACCIÓN CANCELADA: El usuario ha cancelado la acción."
                )
                self._reset_estado()
                return {
                    "estado": "cancelado",
                    "message": mensaje
                }

            else:
                no_entendido = (
                    "No te he entendido. ¿Me confirmas con un 'sí' o 'no'?"
                )
                return {
                    "estado": "confirmación",
                    "message": no_entendido,
                    "comando_pendiente": self.comando_pendiente
                }

        print("\n=== PROCESAMIENTO DE COMANDO ===")
        print(f"Comando original: {respuesta}")
        
        mensaje_ia = enviar_comando_openai(self.usuario_actual, respuesta)
        print(f"Respuesta IA: {mensaje_ia}")

        comando_detectado = self._detectar_accion_en_respuesta(mensaje_ia)
        print(f"Comando detectado: {comando_detectado}")

        if comando_detectado:
            self.comando_pendiente = comando_detectado
            #primero intentar extraer el valor de la respuesta de la IA
            valor_ia = self._extraer_valor_numerico(mensaje_ia)
            if valor_ia is not None:
                self.valor_pendiente = valor_ia
                print(f"Usando valor de la respuesta IA: {self.valor_pendiente} metros")
            else:
                self.valor_pendiente = 3  # Valor por defecto
                print(f"Usando valor por defecto: {self.valor_pendiente} metros")

            if personalidad_actual == "pregunton":
                probabilidad = random()
                print(f"=== EVALUANDO PROBABILIDAD DE PREGUNTA ===")
                print(f"Probabilidad generada: {probabilidad}")

                if probabilidad < 0.5:  # 50% de probabilidad de hacer pregunta
                    print("Generando pregunta educativa")
                    prompt_pregunta = (
                        f" El usuario quiere {self.comando_pendiente}. "
                    "REGLAS ESTRICTAS:\n"
                    "1. NO USES preguntas comunes o repetitivas\n"
                    "2. Alterna entre estas categorías:\n"
                    " Ciencia, historia, geografia y naturaleza\n"
                    "3. La pregunta debe ser específica y tener una única respuesta clara\n"
                    "4. Actúa como un profesor pesado y amenazante\n"
                    "5. Las pregutnas tienen que ser apropiadas para niños"
                    "Ejemplo: '¡Detente! Antes de dejarte conectar, dime: ¿..? (esto es solo un ejemplo," 
                    "peinsa y se original en tus conetstaciones)"
                )
                    pregunta_educativa = enviar_comando_openai(self.usuario_actual, prompt_pregunta)
                    self.estado_conversacion = "pregunta_educativa"
                    return {
                        "estado": "pregunta",
                        "message": pregunta_educativa,
                        "comando_pendiente": self.comando_pendiente,
                        "audio_url": self.text_to_speech(pregunta_educativa)
                    }
                else:
                    print("Caso confirmación normal")
                    prompt_confirmacion = (
                        f"PEDIR_CONFIRMACION: El usuario quiere {self.comando_pendiente}. "
                        "Pregunta si quiere continuar con la acción. "
                        "No hagas ninguna pregunta educativa. Amenaza con que te gusta hacer preguntas "
                        "y en cualquier momento te puede tocar una. Sé original. Máximo 20 tokens. "
                        f"IMPORTANTE: La palabra '{self.comando_pendiente}' DEBE estar en la respuesta."
                    )
                    mensaje_confirmacion = enviar_comando_openai(self.usuario_actual, prompt_confirmacion)
                    self.estado_conversacion = "confirmar_accion"
                    return {
                        "estado": "confirmación",
                        "message": mensaje_confirmacion,
                        "comando_pendiente": self.comando_pendiente,
                        "audio_url": self.text_to_speech(mensaje_confirmacion)
                    }
            
            else:
                self.estado_conversacion = "confirmar_accion"
                return {
                    "estado": "confirmación",
                    "message": mensaje_ia,
                    "comando_pendiente": self.comando_pendiente,
                    "audio_url": self.text_to_speech(mensaje_ia)
                }

        return {
            "estado": "respuesta_general",
            "message": mensaje_ia
        }
        


    def ejecutar_accion(self, accion, metros, es_confirmacion=False):
        """Ejecuta la acción especificada con el dron"""
        from app.voice_control import personalidad_actual
        from app.ModoGlobal import publish_command

        print(f"DEBUG ejecutar_accion: Iniciando acción {accion}")
        try:
            #preparar comando MQTT
            comando_mqtt = None
            if accion == "conectar":
                comando_mqtt = {"action": "conectar"}
                resultado = publish_command(comando_mqtt)
            elif accion == "desconectar":
                comando_mqtt = {"action": "desconectar"}
                resultado = publish_command(comando_mqtt)
            elif accion == "despegar":
                altura = metros if metros is not None else 3
                comando_mqtt = {"action": "despegar", "altura": altura}
                resultado = publish_command(comando_mqtt)
            elif accion == "aterrizar":
                comando_mqtt = {"action": "aterrizar"}
                resultado = publish_command(comando_mqtt)
            elif accion in ["avanzar", "retroceder", "derecha", "izquierda", "subir", "bajar"]:
                direcciones = {
                    "avanzar": "Forward",
                    "retroceder": "Back",
                    "derecha": "Right",
                    "izquierda": "Left",
                    "subir": "Up",
                    "bajar": "Down"
                }
                comando_mqtt = {
                    "action": "mover",
                    "direccion": direcciones[accion],
                    "metros": metros
                }
                resultado = publish_command(comando_mqtt)


            elif accion in ["norte", "sur", "este", "oeste", "noreste", "noroeste", "sureste", "suroeste"]:
                direcciones = {
                    "norte": "North", 
                     "sur": "South", 
                     "este": "East", 
                     "oeste": "West",
                     "noreste": "NorthEast", 
                     "noroeste": "NorthWest", 
                     "sureste": "SouthEast", 
                     "suroeste": "SouthWest"
                }
                comando_mqtt = {
                    "action": "mover",
                    "direccion": direcciones[accion],
                    "metros": metros
                }
                resultado = publish_command(comando_mqtt)

            elif accion == "rotar derecha":
                comando_mqtt = {
                    "action": "rotar",
                    "grados": metros,
                    "direccion": "derecha"
                }
                resultado = publish_command(comando_mqtt)
            elif accion == "rotar izquierda":
                comando_mqtt = {
                    "action": "rotar",
                    "grados": -metros,  # negativo para izquierda
                    "direccion": "izquierda"
                }
                resultado = publish_command(comando_mqtt)
            elif accion == "rotar":  # sin dirección especificada, usar derecha por defecto
                comando_mqtt = {
                    "action": "rotar",
                    "grados": metros,
                    "direccion": "derecha"
                }
                resultado = publish_command(comando_mqtt)
            else:
                return {"estado": "error", "message": "Acción no reconocida"}


            print(f"DEBUG: Resultado de la publicacion: {resultado}")
            if resultado and resultado["estado"] == "success":
                print("DEBUG: Acción publicada exitosamente")

            if not app.ModoGlobal.evento_accion.wait(timeout=30):
                print("ERROR: No se recibió respuesta del dron")
                return {"estado": "error", "message": "No se recibió respuesta del dron"}

            print(f"DEBUG: Resultado de la accion: {app.ModoGlobal.resultado_accion}")

            if personalidad_actual == "pregunton":
                if es_confirmacion and app.ModoGlobal.resultado_accion["estado"]== "success":
                    prompt_accion = (
                        f"ACCIÓN COMPLETADA: La acción '{accion}' se ha completado.\n"
                        "REGLAS:\n"
                        "- Solo menciona que la acción se ha completado\n"
                        "- NO uses la palabra 'correcto' ni felicites\n"
                        "- Amenaza con futuras preguntas de forma juguetona\n"
                        "- TERMINA preguntando qué quiere hacer ahora\n"
                        "- Máximo dos frases en total"
                    )

                else:  # caso para respuestas correctas a preguntas educativas
                    prompt_accion = (
                        f"ACCIÓN COMPLETADA: La acción '{accion}' se ha completado.\n"
                        "REGLAS:\n"
                        "- Felicita al usuario por su respuesta correcta con mucho entusiasmo\n"
                        "- Luego menciona que la acción se ha completado con éxito\n"
                        "- Después amenaza con futuras preguntas de forma juguetona\n"
                        "- TERMINA preguntando qué quiere hacer ahora\n"
                        "- Máximo tres frases en total"

                    )


                mensaje = enviar_comando_openai(self.usuario_actual, prompt_accion)
                self._reset_estado()
                app.ModoGlobal.resultado_accion = None
                app.ModoGlobal.evento_accion.clear()
                return {"estado": "success", "message": mensaje}

            elif personalidad_actual == "normal" or "gracioso" or "borde":
                if app.ModoGlobal.resultado_accion["estado"] == "success":
                    prompt_accion = (
                    f"ACCIÓN COMPLETADA: La acción '{accion}' se ha completado.\n"
                    "REGLAS:\n"
                    "- Solo menciona que la acción se ha completado\n"
                    "- NO uses la palabra 'correcto' ni felicites\n"
                    "- TERMINA preguntando qué quiere hacer ahora\n"
                    "- Máximo dos frases en total"
                )
                    mensaje = enviar_comando_openai(self.usuario_actual, prompt_accion)
                    self._reset_estado()
                    app.ModoGlobal.resultado_accion=None
                    app.ModoGlobal.evento_accion.clear()
                    return {"estado": "success", "message": mensaje}
                else:
                        prompt_error = (
                            f"La acción '{accion}' no se pudo completar.\n"
                            "REGLAS ESTRICTAS:\n"
                            "- SOLO informa del error\n"
                            "- NO hagas preguntas educativas\n"
                            "- NO sugieras otras acciones\n"
                            "- NO uses emojis\n"
                            "- NO intentes animar o consolar\n"
                            "- NO menciones retos o pruebas\n"
                            "- Sé breve y directo"
                        )
                        mensaje = enviar_comando_openai(self.usuario_actual, prompt_error)
                        self._reset_estado()
                        app.ModoGlobal.resultado_accion=None
                        app.ModoGlobal.evento_accion.clear()
                        return {"estado": "error", "message": mensaje}

        except Exception as e:
            print(f"Error al ejecutar acción {accion}: {e}")
            prompt_error = f"ERROR EN ACCIÓN: Ocurrió un error inesperado al intentar {accion}."
            mensaje = enviar_comando_openai(self.usuario_actual, prompt_error)
            self._reset_estado()
            app.ModoGlobal.resultado_accion=None
            return {"estado": "error", "message": mensaje}

    def _reset_estado(self):
        """Resetea el estado de la conversación"""
        self.estado_conversacion = None
        self.comando_pendiente = None
        self.valor_pendiente = None

    def text_to_speech(self, text):
        """Convierte texto a audio usando gTTS"""
        try:
            mp3_fp = BytesIO()
            tts = gTTS(text=text, lang='es', slow=False)
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            audio_base64 = base64.b64encode(mp3_fp.read()).decode()
            return f"data:audio/mp3;base64,{audio_base64}"
        except Exception as e:
            print(f"Error en text_to_speech: {e}")
            return None

    def cambiar_personalidad(self, user_id, nueva_personalidad):
        """Cambia la personalidad del asistente"""
        from app.voice_control import cambiar_personalidad as cambiar_personalidad_vc
        return cambiar_personalidad_vc(user_id, nueva_personalidad)



    

    
    