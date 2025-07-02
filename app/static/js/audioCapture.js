// audioCapture.js
class AudioCapture {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.stream = null;
        this.isInitialized = false;
    }

    async initializeRecording() {
        if (this.isInitialized) return true;
        
        try {
            const hablarBtn = document.getElementById('hablar-btn');
            if (hablarBtn) {
                hablarBtn.textContent = "Iniciando...";
                hablarBtn.disabled = true;
            }

            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: true,
                video: false
            });
            
            this.mediaRecorder = new MediaRecorder(this.stream);
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                await this.sendAudioToServer(audioBlob);
                this.audioChunks = [];
            };

            this.isInitialized = true;

            if (hablarBtn) {
                hablarBtn.textContent = "Mantén para hablar";
                hablarBtn.disabled = false;
            }

            return true;
        } catch (error) {
            console.error('Error al inicializar la grabación:', error);
            const hablarBtn = document.getElementById('hablar-btn');
            if (hablarBtn) {
                hablarBtn.textContent = "Error - No hay micrófono";
                hablarBtn.disabled = true;
            }
            return false;
        }
    }

    async startRecording() {
        try {
            if (!this.isInitialized) {
                await this.initializeRecording();
            }

            if (this.mediaRecorder && !this.isRecording) {
                this.audioChunks = [];
                this.mediaRecorder.start();
                this.isRecording = true;
                
                const hablarBtn = document.getElementById('hablar-btn');
                if (hablarBtn) {
                    hablarBtn.textContent = "Escuchando...";
                    hablarBtn.classList.add('recording');
                }
            }
        } catch (error) {
            console.error('Error al iniciar la grabación:', error);
            const hablarBtn = document.getElementById('hablar-btn');
            if (hablarBtn) {
                hablarBtn.textContent = "Error - Intenta de nuevo";
            }
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            const hablarBtn = document.getElementById('hablar-btn');
            if (hablarBtn) {
                hablarBtn.textContent = "Mantén para hablar";
                hablarBtn.classList.remove('recording');
            }
        }
    }

    async sendAudioToServer(audioBlob) {
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            const response = await fetch('/procesar_audio_cliente', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.transcription) {
                const transcrito = data.transcription;
                const textoTranscritoEl = document.getElementById('texto-transcrito');
                const comandoTextoEl = document.getElementById('comando-texto');
    
                if (textoTranscritoEl) textoTranscritoEl.textContent = transcrito;
                if (comandoTextoEl) comandoTextoEl.value = transcrito;
    
                await this.procesarComando(transcrito);
            }
        } catch (error) {
            console.error('Error al enviar audio al servidor:', error);
            document.getElementById('texto-transcrito').textContent = 
                'Error al procesar el audio. Por favor, intenta de nuevo.';
        }
    }

    async procesarComando(transcripcion) {
        try {
            const response = await fetch('/enviar_comandoIA', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ comando: transcripcion })
            });
    
            const data = await response.json();
    
            if (data.message) {
                document.getElementById('texto-respuesta').textContent = data.message;
            }
    
            if (data.audio_url) {
                const event = new CustomEvent('playAudio', { 
                    detail: { url: data.audio_url } 
                });
                document.dispatchEvent(event);
            }
        } catch (error) {
            console.error('Error al procesar comando:', error);
        }
    }
}

export default AudioCapture;