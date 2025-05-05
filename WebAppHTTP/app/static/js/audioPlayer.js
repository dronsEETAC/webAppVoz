// AudioPlayer.js

class AudioPlayer {
    constructor() {
        this.audioContext = null;
        this.audioElement = null;
        this.isInitialized = false;
        this.initializationAttempted = false;
        this.queue = [];
        this.isPlaying = false;
        
        this.audioElement = new Audio();
        this.audioElement.playbackRate = 1.4;
        this.audioElement.preload = 'auto';
        this.audioElement.playsInline = true;
        
        this.initialize = this.initialize.bind(this);
        this.play = this.play.bind(this);
        this.handlePlayEnd = this.handlePlayEnd.bind(this);
        
        this.audioElement.addEventListener('ended', this.handlePlayEnd);
        this.audioElement.addEventListener('error', (e) => {
            console.error('Error en reproducción de audio:', e);
            this.handlePlayEnd();
        });
        
        this.initialize();
        
        document.addEventListener('playAudio', (event) => {
            if (event.detail && event.detail.url) {
                this.play(event.detail.url);
            }
        });
    }

    async initialize() {
        if (this.isInitialized || this.initializationAttempted) return;
        
        this.initializationAttempted = true;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const enableAudio = async () => {
                try {
                    if (this.audioContext.state === 'suspended') {
                        await this.audioContext.resume();
                    }
                    this.isInitialized = true;
                    
                    document.removeEventListener('touchstart', enableAudio, true);
                    document.removeEventListener('touchend', enableAudio, true);
                    document.removeEventListener('click', enableAudio, true);
                    
                    this.processQueue();
                } catch (error) {
                    console.error('Error al habilitar audio:', error);
                }
            };
            
            document.addEventListener('touchstart', enableAudio, true);
            document.addEventListener('touchend', enableAudio, true);
            document.addEventListener('click', enableAudio, true);
            
        } catch (error) {
            console.error('Error al inicializar AudioPlayer:', error);
        }
    }

    async play(url) {

        this.queue.push(url);
        
        if (!this.isInitialized) {
            await this.initialize();
            return;
        }
        
        if (!this.isPlaying) {
            this.processQueue();
        }
    }

    async processQueue() {
        if (this.isPlaying || this.queue.length === 0) return;
        
        try {
            this.isPlaying = true;
            const url = this.queue[0];

            this.audioElement.src = url;
            this.audioElement.playbackRate = 1.35
            
            try {
                await this.audioElement.play();
                console.log('Reproduciendo audio:', url);
            } catch (error) {
                console.error('Error al reproducir audio:', error);
                this.handlePlayEnd();
            }
            
        } catch (error) {
            console.error('Error al procesar cola de audio:', error);
            this.handlePlayEnd();
        }
    }

    handlePlayEnd() {

        if (this.queue.length > 0) {
            this.queue.shift();
        }
        
        this.isPlaying = false;
        
        this.processQueue();
    }
}


const audioPlayer = new AudioPlayer();
export default audioPlayer;