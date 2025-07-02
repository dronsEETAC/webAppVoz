import os
import tempfile
import subprocess
import json
import wave
from datetime import datetime
from vosk import Model, KaldiRecognizer

class AudioProcessor:
    def __init__(self):
        try:
            self._log_debug("Inicializando AudioProcessor...")
            self.ffmpeg_path = self._get_ffmpeg_path()
            self.model_path = "vosk-model-small-es-0.42"
            self._verify_ffmpeg()
            self._log_debug("AudioProcessor inicializado correctamente")
        except Exception as e:
            self._log_debug(f"Error durante la inicialización de AudioProcessor: {str(e)}")
            raise
        
    def _log_debug(self, message):
        """Función de logging simple"""
        print(f"[DEBUG] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")

    def _get_ffmpeg_path(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        possible_paths = [
            os.path.join(base_dir, 'bin', 'ffmpeg.exe'),
            os.path.join(base_dir, 'tools', 'ffmpeg.exe'),
            os.path.join(base_dir, 'ffmpeg.exe'),
            os.path.join(base_dir, 'ffmpeg_files', 'ffmpeg.exe')
        ]
        
        self._log_debug(f"Buscando FFmpeg en: {possible_paths}")
        
        for path in possible_paths:
            if os.path.exists(path):
                self._log_debug(f"FFmpeg encontrado en: {path}")
                return path
        
        raise Exception("No se encontró FFmpeg en ninguna ubicación esperada")

    def _create_temp_files(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        webm_path = os.path.join(tempfile.gettempdir(), f'audio_{timestamp}.webm')
        wav_path = os.path.join(tempfile.gettempdir(), f'audio_{timestamp}.wav')
        return webm_path, wav_path

    def _convert_to_wav(self, webm_path, wav_path):
        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-i', webm_path,
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            wav_path,
            '-y'
        ]
        
        self._log_debug(f"Ejecutando FFmpeg: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)
        self._log_debug("Conversión FFmpeg completada")

    def _transcribe_audio(self, wav_path):
        self._log_debug("Iniciando procesamiento con Vosk")
        with wave.open(wav_path, "rb") as wf:
            if not os.path.exists(self.model_path):
                self._log_debug(f"Modelo Vosk no encontrado en: {self.model_path}")
                raise Exception(f"No se encontró el modelo Vosk en {self.model_path}")
            
            self._log_debug("Modelo Vosk cargado")
            recognizer = KaldiRecognizer(Model(self.model_path), 16000)
            transcription = []

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    if result.get('text', '').strip():
                        transcription.append(result['text'])

            final_result = json.loads(recognizer.FinalResult())
            if final_result.get('text', '').strip():
                transcription.append(final_result['text'])

            return ' '.join(transcription) if transcription else ''

    def _cleanup_files(self, *files):
        for file_path in files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    self._log_debug(f"Archivo eliminado: {file_path}")
            except Exception as e:
                self._log_debug(f"Error al eliminar archivo {file_path}: {e}")

    def process_audio(self, audio_data):
        #procesa un archivo de audio y retorna su transcripción.
           
        if not audio_data:
            return {'success': False, 'error': 'No se recibieron datos de audio'}
            
        self._log_debug(f"Recibidos {len(audio_data)} bytes de audio")
        
        webm_path, wav_path = self._create_temp_files()
        
        try:
            with open(webm_path, 'wb') as f:
                f.write(audio_data)
            
            file_size = os.path.getsize(webm_path)
            self._log_debug(f"Archivo webm guardado, tamaño: {file_size} bytes")
            
            if file_size == 0:
                raise Exception("El archivo de audio está vacío")

            self._convert_to_wav(webm_path, wav_path)
            
            if not os.path.exists(wav_path):
                raise Exception("El archivo WAV no se creó")
            
            wav_size = os.path.getsize(wav_path)
            self._log_debug(f"Archivo WAV creado, tamaño: {wav_size} bytes")
            
            if wav_size == 0:
                raise Exception("El archivo WAV está vacío")

            transcription = self._transcribe_audio(wav_path)
            self._log_debug(f"Transcripción completada: {transcription}")

            return {
                'success': True,
                'transcription': transcription    
            }

        except Exception as e:
            self._log_debug(f"Error en el procesamiento: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            self._cleanup_files(webm_path, wav_path)

    def _verify_ffmpeg(self):
        """Verifica que FFmpeg funciona correctamente"""
        try:
            self._log_debug(f"Verificando FFmpeg en: {self.ffmpeg_path}")
            
            if not os.path.exists(self.ffmpeg_path):
                raise Exception(f"FFmpeg no encontrado en: {self.ffmpeg_path}")
            
            self._log_debug("FFmpeg existe, verificando permisos...")
            
            if not os.access(self.ffmpeg_path, os.X_OK):
                self._log_debug("FFmpeg no tiene permisos de ejecución")
                if os.name == 'nt':
                    try:
                        import stat
                        os.chmod(self.ffmpeg_path, stat.S_IEXEC)
                        self._log_debug("Permisos de ejecución añadidos")
                    except Exception as e:
                        self._log_debug(f"No se pudieron modificar los permisos: {e}")
            
            self._log_debug("Intentando ejecutar FFmpeg para verificar...")
            
            try:
                with open(os.devnull, 'w') as devnull:
                    subprocess.run(
                        [self.ffmpeg_path, '-version'],
                        stdout=devnull,
                        stderr=devnull,
                        check=True
                    )
                self._log_debug("FFmpeg ejecutado correctamente")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Error al ejecutar FFmpeg: {str(e)}")
            except Exception as e:
                raise Exception(f"Error inesperado al ejecutar FFmpeg: {str(e)}")

        except Exception as e:
            self._log_debug(f"Error en verificación de FFmpeg: {str(e)}")
            raise